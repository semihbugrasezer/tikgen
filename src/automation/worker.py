from PyQt5.QtCore import QThread, pyqtSignal
import logging
import gc
import psutil
import time
import traceback
import json
import os
import random
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from queue import PriorityQueue
import sys

# Add the project root directory to Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.utils.database import Session, Pin, DatabaseManager, db_manager
from src.utils.config import get_config
from src.automation.content_generator import ContentGenerator
from src.automation.integrations import WordPressIntegration, PinterestIntegration

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class TaskConfig:
    """Configuration for automated tasks"""

    def __init__(
        self,
        name: str,
        description: str,
        function,
        dependencies: List[str] = None,
        schedule: Dict[str, bool] = None,
        retry_count: int = 3,
        timeout: int = 300,
    ):
        self.name = name
        self.description = description
        self.function = function
        self.dependencies = dependencies or []
        self.schedule = schedule or {
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": True,
            "friday": True,
            "saturday": False,
            "sunday": False,
        }
        self.retry_count = retry_count
        self.timeout = timeout
        self.enabled = True
        self.last_run = None
        self.next_run = None
        self.success_count = 0
        self.failure_count = 0
        self.total_runtime = 0

    def to_dict(self) -> dict:
        """Convert task config to dictionary for storage"""
        return {
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "schedule": self.schedule,
            "retry_count": self.retry_count,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_runtime": self.total_runtime,
        }

    @classmethod
    def from_dict(cls, data: dict, function) -> "TaskConfig":
        """Create task config from dictionary"""
        task = cls(
            name=data["name"],
            description=data["description"],
            function=function,
            dependencies=data.get("dependencies", []),
            schedule=data.get("schedule", {}),
            retry_count=data.get("retry_count", 3),
            timeout=data.get("timeout", 300),
        )
        task.enabled = data.get("enabled", True)
        task.last_run = (
            datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None
        )
        task.next_run = (
            datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None
        )
        task.success_count = data.get("success_count", 0)
        task.failure_count = data.get("failure_count", 0)
        task.total_runtime = data.get("total_runtime", 0)
        return task


class AutomationWorker(QThread):
    """Enhanced worker thread for handling automated tasks"""

    # Signals
    status_changed = pyqtSignal(
        str, bool, bool
    )  # Worker status updates (message, running, paused)
    progress_updated = pyqtSignal(int, int)  # Progress updates (current, total)
    task_completed = pyqtSignal(str, bool, str)  # Task name, success, message
    task_progress = pyqtSignal(
        str, int, str
    )  # Task name, progress percentage, status message
    error_occurred = pyqtSignal(str)  # Error messages
    queue_updated = pyqtSignal(list)  # List of queued tasks

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.running = False
        self.paused = False
        self.memory_threshold_mb = 500
        self.process = psutil.Process()
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        self.task_queue = PriorityQueue()
        self.task_configs = {}
        self.running_tasks = set()  # Track currently running tasks
        self.task_history = {}
        self.config_file = "task_configs.json"
        self.selenium_driver = None
        self.config = self._load_config()
        self.wordpress_integrations = {}
        self.pinterest_integration = None
        self.content_generator = None
        self._init_integrations()
        self._init_default_tasks()

    def _init_integrations(self):
        """Initialize all integrations with improved error handling"""
        try:
            # Initialize WordPress integrations for each site
            for site in self.config.get("wordpress_sites", []):
                site_id = f"{site['url']}_{site['category']}"
                self.wordpress_integrations[site_id] = WordPressIntegration(
                    url=site["url"],
                    username=site["username"],
                    password=site["password"],
                    category=site["category"],
                )
                logger.info(
                    f"Initialized WordPress integration for {site['url']} with category {site['category']}"
                )

            # Initialize Pinterest integration with spam avoidance settings
            pinterest_config = self.config.get("pinterest", {})
            if pinterest_config.get("access_token"):
                self.pinterest_integration = PinterestIntegration(
                    access_token=pinterest_config.get("access_token"),
                    email=pinterest_config.get("email", ""),
                    password=pinterest_config.get("password", ""),
                    default_board=pinterest_config.get("default_board", "AutoPinner"),
                    avoid_spam=pinterest_config.get("avoid_spam", {}),
                )
                logger.info("Initialized Pinterest integration")
            else:
                logger.warning("Pinterest access token not found in config")

            # Initialize content generator with OpenRouter
            content_config = self.config.get("content_generation", {})
            self.content_generator = ContentGenerator(content_config)
            logger.info("Initialized OpenRouter content generator")

        except Exception as e:
            logger.error(f"Error initializing integrations: {e}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(f"Failed to initialize integrations: {str(e)}")

    def _init_default_tasks(self):
        """Initialize default task configurations"""
        self.task_configs = {
            "generate_content": TaskConfig(
                name="generate_content",
                description="Generate content using AI",
                function=self.generate_content,
                schedule={"monday": True, "wednesday": True, "friday": True},
            ),
            "publish_to_wordpress": TaskConfig(
                name="publish_to_wordpress",
                description="Publish content to WordPress",
                function=self.publish_to_wordpress,
                dependencies=["generate_content"],
                schedule={"tuesday": True, "thursday": True},
            ),
            "share_on_pinterest": TaskConfig(
                name="share_on_pinterest",
                description="Share content on Pinterest",
                function=self.share_on_pinterest,
                dependencies=["generate_content"],
                schedule={"tuesday": True, "thursday": True},
            ),
            "analyze_trends": TaskConfig(
                name="analyze_trends",
                description="Analyze Pinterest trends",
                function=self.analyze_trends,
                schedule={"monday": True},
            ),
            "collect_stats": TaskConfig(
                name="collect_stats",
                description="Collect performance statistics",
                function=self.collect_stats,
                schedule={"friday": True},
            ),
        }

    def _load_task_configs(self):
        """Load task configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    for task_name, task_data in data.items():
                        if task_name in self.task_configs:
                            self.task_configs[task_name] = TaskConfig.from_dict(
                                task_data, self.task_configs[task_name].function
                            )
                logger.info("Task configurations loaded")
        except Exception as e:
            logger.error(f"Error loading task configurations: {e}")

    def _save_task_configs(self):
        """Save task configurations to file"""
        try:
            data = {name: task.to_dict() for name, task in self.task_configs.items()}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Task configurations saved")
        except Exception as e:
            logger.error(f"Error saving task configurations: {e}")

    def run(self):
        """Main worker loop"""
        self.running = True
        self.status_changed.emit("Running", True, False)

        try:
            while self.running:
                if not self.paused:
                    self._process_task_queue()
                    self._schedule_pending_tasks()
                time.sleep(1)  # Check every second

        except Exception as e:
            logger.error(f"Worker error: {e}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(f"Worker error: {str(e)}")

        finally:
            self._save_task_configs()
            self.running = False
            self.status_changed.emit("Stopped", False, False)

    def _process_task_queue(self):
        """Process queued tasks"""
        while not self.task_queue.empty():
            priority, task_name = self.task_queue.get()
            task = self.task_configs.get(task_name)

            if not task or not task.enabled or task_name in self.running_tasks:
                continue

            if not self._can_run_task(task):
                self.task_queue.put((priority, task_name))
                continue

            self.running_tasks.add(task_name)
            self._execute_task(task)
            self.running_tasks.remove(task_name)

    def _can_run_task(self, task: TaskConfig) -> bool:
        """Check if a task can be run based on dependencies"""
        for dep in task.dependencies:
            dep_task = self.task_configs.get(dep)
            if not dep_task or not dep_task.last_run:
                return False
            if dep in self.running_tasks:
                return False
        return True

    def _execute_task(self, task: TaskConfig):
        """Execute a task with retry logic"""
        start_time = time.time()
        retries = 0
        success = False
        message = ""

        while retries < task.retry_count and not success:
            try:
                self.task_progress.emit(task.name, 0, "Starting task")
                task.function()
                success = True
                message = "Task completed successfully"
                task.success_count += 1
            except Exception as e:
                retries += 1
                message = f"Error: {str(e)}"
                logger.error(f"Task {task.name} failed: {e}")
                time.sleep(5)  # Wait before retrying

        if not success:
            task.failure_count += 1
            self.error_occurred.emit(
                f"Task {task.name} failed after {retries} attempts"
            )

        task.last_run = datetime.now()
        self._save_task_history(task, start_time)
        self.task_completed.emit(task.name, success, message)

    def _schedule_pending_tasks(self):
        """Schedule tasks based on their configuration"""
        now = datetime.now()
        day_name = now.strftime("%A").lower()

        for task_name, task in self.task_configs.items():
            if not task.enabled:
                continue

            if task.schedule.get(day_name, False):
                if not task.last_run or (now - task.last_run).days >= 1:
                    self.task_queue.put((1, task_name))

    def _save_task_history(self, task: TaskConfig, start_time: float):
        """Save task execution history"""
        end_time = time.time()
        runtime = end_time - start_time
        task.total_runtime += runtime

        if task.name not in self.task_history:
            self.task_history[task.name] = []

        self.task_history[task.name].append(
            {
                "timestamp": datetime.now().isoformat(),
                "runtime": runtime,
                "success": task.success_count > task.failure_count,
            }
        )

        # Keep only the last 100 executions
        if len(self.task_history[task.name]) > 100:
            self.task_history[task.name] = self.task_history[task.name][-100:]

    def get_task_stats(self, task_name: str) -> Optional[dict]:
        """Get statistics for a specific task"""
        task = self.task_configs.get(task_name)
        if not task:
            return None

        history = self.task_history.get(task_name, [])
        success_rate = (
            task.success_count / (task.success_count + task.failure_count) * 100
            if (task.success_count + task.failure_count) > 0
            else 0
        )

        return {
            "name": task.name,
            "description": task.description,
            "enabled": task.enabled,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "success_count": task.success_count,
            "failure_count": task.failure_count,
            "success_rate": success_rate,
            "total_runtime": task.total_runtime,
            "history": history,
        }

    def get_queue_status(self) -> list:
        """Get current queue status"""
        queue_items = []
        while not self.task_queue.empty():
            priority, task_name = self.task_queue.get()
            queue_items.append({"task": task_name, "priority": priority})
            self.task_queue.put((priority, task_name))
        return queue_items

    def set_task_schedule(self, task_name: str, schedule: Dict[str, bool]):
        """Set schedule for a task"""
        if task_name in self.task_configs:
            self.task_configs[task_name].schedule = schedule
            self._save_task_configs()

    def set_task_dependencies(self, task_name: str, dependencies: List[str]):
        """Set dependencies for a task"""
        if task_name in self.task_configs:
            self.task_configs[task_name].dependencies = dependencies
            self._save_task_configs()

    def set_task_config(
        self, task_name: str, retry_count: int = None, timeout: int = None
    ):
        """Set configuration for a task"""
        if task_name in self.task_configs:
            if retry_count is not None:
                self.task_configs[task_name].retry_count = retry_count
            if timeout is not None:
                self.task_configs[task_name].timeout = timeout
            self._save_task_configs()

    def generate_content(self):
        """Generate content for all WordPress sites"""
        try:
            self.task_progress.emit(
                "content_generation", 0, "Starting content generation"
            )

            for site_id, integration in self.wordpress_integrations.items():
                site_config = next(
                    (
                        site
                        for site in self.config.get("wordpress_sites", [])
                        if f"{site['url']}_{site['category']}" == site_id
                    ),
                    None,
                )

                if not site_config:
                    continue

                # Generate article
                self.task_progress.emit(
                    "content_generation",
                    25,
                    f"Generating article for {site_config['url']}",
                )

                article = self.content_generator.generate_article(
                    category=site_config["category"],
                    length=int(
                        self.config.get("content_generation", {}).get(
                            "article_length", "1000"
                        )
                    ),
                )

                # Generate images
                self.task_progress.emit(
                    "content_generation",
                    50,
                    f"Generating images for {site_config['url']}",
                )

                images = self.content_generator.generate_images(
                    article=article,
                    style=self.config.get("content_generation", {}).get(
                        "image_style", "realistic"
                    ),
                    count=int(
                        self.config.get("content_generation", {}).get(
                            "max_images_per_article", "3"
                        )
                    ),
                )

                # Save to database
                self.task_progress.emit(
                    "content_generation", 75, f"Saving content for {site_config['url']}"
                )

                pin = Pin(
                    title=article["title"],
                    description=article["content"],
                    images=images,
                    status="pending",
                    wordpress_site=site_config["url"],
                    category=site_config["category"],
                )
                self.db.add_pin(pin)

                self.task_progress.emit(
                    "content_generation",
                    100,
                    f"Content generated for {site_config['url']}",
                )

            self.task_completed.emit(
                "content_generation", True, "Content generation completed"
            )

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(f"Content generation failed: {str(e)}")
            self.task_completed.emit("content_generation", False, str(e))

    def publish_to_wordpress(self):
        """Publish content to WordPress sites with improved scheduling"""
        try:
            self.task_progress.emit(
                "wordpress_posting", 0, "Starting WordPress publishing"
            )

            for site_id, integration in self.wordpress_integrations.items():
                site_config = next(
                    (
                        site
                        for site in self.config.get("wordpress_sites", [])
                        if f"{site['url']}_{site['category']}" == site_id
                    ),
                    None,
                )

                if not site_config:
                    continue

                # Get pending pins for this site
                pending_pins = self.db.get_pending_pins(
                    wordpress_site=site_config["url"],
                    limit=int(site_config.get("max_posts_per_day", "4")),
                )

                total_pins = len(pending_pins)
                for index, pin in enumerate(pending_pins):
                    try:
                        # Add random delay between posts
                        delay = random.randint(5, 15)
                        time.sleep(delay)

                        self.task_progress.emit(
                            "wordpress_posting",
                            int((index / total_pins) * 100),
                            f"Publishing to {site_config['url']}: {pin.title}",
                        )

                        # Publish to WordPress
                        post_url = integration.create_post(
                            title=pin.title,
                            content=pin.description,
                            images=pin.images,
                            category=site_config["category"],
                        )

                        # Update pin status
                        pin.status = "published"
                        pin.wordpress_url = post_url
                        self.db.update_pin(pin)

                    except Exception as e:
                        logger.error(f"Error publishing pin {pin.id}: {e}")
                        pin.status = "failed"
                        self.db.update_pin(pin)
                        continue

            self.task_completed.emit(
                "wordpress_posting", True, "WordPress publishing completed"
            )

        except Exception as e:
            logger.error(f"Error in WordPress publishing: {e}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(f"WordPress publishing failed: {str(e)}")
            self.task_completed.emit("wordpress_posting", False, str(e))

    def share_on_pinterest(self):
        """Share content on Pinterest with improved spam avoidance"""
        try:
            self.task_progress.emit(
                "pinterest_pinning", 0, "Starting Pinterest sharing"
            )

            # Get published pins that haven't been shared on Pinterest
            pins = self.db.get_pins_by_status("published", limit=20)
            total_pins = len(pins)

            for index, pin in enumerate(pins):
                try:
                    # Add random delay between pins
                    delay = random.randint(
                        int(
                            self.config.get("pinterest", {})
                            .get("avoid_spam", {})
                            .get("min_delay", "15")
                        ),
                        int(
                            self.config.get("pinterest", {})
                            .get("avoid_spam", {})
                            .get("max_delay", "45")
                        ),
                    )
                    time.sleep(delay)

                    self.task_progress.emit(
                        "pinterest_pinning",
                        int((index / total_pins) * 100),
                        f"Sharing on Pinterest: {pin.title}",
                    )

                    # Share on Pinterest with random board rotation
                    if (
                        self.config.get("pinterest", {})
                        .get("avoid_spam", {})
                        .get("rotate_boards", "true")
                        == "true"
                    ):
                        board = self.pinterest_integration.get_random_board()
                    else:
                        board = self.config.get("pinterest", {}).get(
                            "default_board", "AutoPinner"
                        )

                    pin_url = self.pinterest_integration.create_pin(
                        title=pin.title,
                        description=pin.description,
                        image_url=pin.images[0],
                        board_name=board,
                        article_url=pin.wordpress_url,
                    )

                    # Update pin status
                    pin.status = "shared"
                    pin.pinterest_url = pin_url
                    self.db.update_pin(pin)

                except Exception as e:
                    logger.error(f"Error sharing pin {pin.id}: {e}")
                    pin.status = "failed"
                    self.db.update_pin(pin)
                    continue

            self.task_completed.emit(
                "pinterest_pinning", True, "Pinterest sharing completed"
            )

        except Exception as e:
            logger.error(f"Error in Pinterest sharing: {e}")
            logger.error(traceback.format_exc())
            self.error_occurred.emit(f"Pinterest sharing failed: {str(e)}")
            self.task_completed.emit("pinterest_pinning", False, str(e))

    def _generate_keywords_for_domain(self, domain: str) -> List[str]:
        """Generate keywords for a domain"""
        # This is a simple implementation - you can enhance it with more sophisticated keyword generation
        base_keywords = [
            "best",
            "top",
            "guide",
            "tips",
            "how to",
            "why",
            "what is",
            "examples",
            "tutorial",
            "review",
            "comparison",
            "vs",
        ]

        domain_keywords = domain.split()
        keywords = []

        # Generate combinations
        for base in base_keywords:
            for domain_kw in domain_keywords:
                keywords.append(f"{base} {domain_kw}")

        # Add some domain-specific keywords
        keywords.extend(domain_keywords)

        # Return a random selection
        return random.sample(keywords, min(10, len(keywords)))

    def _load_config(self) -> Dict:
        """Load configuration from file"""
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                return json.load(f)
        return {}

    def analyze_trends(self):
        """Analyze Pinterest trends"""
        self.task_progress.emit("analyze_trends", 10, "Analyzing Pinterest trends")
        # Implementation here
        self.task_progress.emit("analyze_trends", 100, "Trend analysis completed")

    def collect_stats(self):
        """Collect performance statistics"""
        self.task_progress.emit("collect_stats", 10, "Collecting statistics")
        # Implementation here
        self.task_progress.emit("collect_stats", 100, "Statistics collected")

    def get_status(self):
        """Get current worker status"""
        return {
            "running": self.running,
            "paused": self.paused,
            "queue_size": self.task_queue.qsize(),
            "running_tasks": list(self.running_tasks),
        }

    def stop(self):
        """Stop the worker"""
        self.running = False
        self.cleanup_resources()
        self.wait()

    def pause(self):
        """Pause the worker"""
        self.paused = True
        self.status_changed.emit("Paused", True, True)

    def resume(self):
        """Resume the worker"""
        self.paused = False
        self.status_changed.emit("Running", True, False)

    def cleanup_resources(self):
        """Clean up resources"""
        # Close Selenium driver if it exists
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except Exception as e:
                logger.error(f"Error closing Selenium driver: {e}")
            finally:
                self.selenium_driver = None

        # Force garbage collection
        gc.collect()

        # Log memory usage
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        logger.info(f"Memory usage after cleanup: {memory_mb:.2f} MB")
