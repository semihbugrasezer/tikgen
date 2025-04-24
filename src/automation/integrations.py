from typing import Dict, List, Optional
import logging
import requests
from datetime import datetime
import json
import os
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts, media
from PIL import Image
import io
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WordPressIntegration:
    """Integration with WordPress sites with optimized memory management"""

    def __init__(self, url: str, username: str, password: str, category: str = None):
        """Initialize WordPress integration with improved memory management"""
        self.url = url.rstrip("/")  # Remove trailing slash
        self.username = username
        self.password = password
        self.category = category
        self.client = None
        self.use_rest_api = False
        self.timeout = 30  # Increased timeout
        self.max_retries = 2  # Reduced retries
        self._session = None
        self._last_connection_time = 0
        self._connection_cache_time = 300  # 5 minutes cache

    @property
    def session(self):
        """Lazy initialization of session"""
        if self._session is None:
            self._session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session

    def _init_connection(self):
        """Initialize connection with memory optimization"""
        current_time = time.time()

        # Check if we need to reconnect
        if (
            (self.client or self.use_rest_api)
            and current_time - self._last_connection_time < self._connection_cache_time
        ):
            return

        # Try REST API first as it's more reliable
        try:
            response = self.session.get(
                f"{self.url}/wp-json/wp/v2/posts",
                auth=(self.username, self.password),
                timeout=self.timeout,
                verify=False,
            )
            if response.status_code == 200:
                self.use_rest_api = True
                self._last_connection_time = current_time
                logger.info(
                    f"Successfully connected to WordPress site {self.url} using REST API"
                )
                return
        except Exception as rest_error:
            logger.warning(f"REST API connection failed: {str(rest_error)}")

        # If REST API fails, try XML-RPC
        for attempt in range(self.max_retries):
            try:
                # Try XML-RPC with increased timeout
                self.client = Client(
                    f"{self.url}/xmlrpc.php", self.username, self.password
                )

                # Test connection with timeout handling
                try:
                    self.client.call(posts.GetPosts({"number": 1}))
                    logger.info(
                        f"Successfully connected to WordPress site {self.url} using XML-RPC"
                    )
                    self._last_connection_time = current_time
                    return
                except Exception as e:
                    logger.warning(f"XML-RPC test call failed: {str(e)}")
                    raise

            except Exception as e:
                logger.warning(
                    f"XML-RPC connection attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt == self.max_retries - 1:
                    # If both REST API and XML-RPC fail, try REST API one more time
                    try:
                        response = self.session.get(
                            f"{self.url}/wp-json/wp/v2/posts",
                            auth=(self.username, self.password),
                            timeout=self.timeout,
                            verify=False,
                        )
                        if response.status_code == 200:
                            self.use_rest_api = True
                            self._last_connection_time = current_time
                            logger.info(
                                f"Successfully connected to WordPress site {self.url} using REST API"
                            )
                            return
                    except Exception as final_error:
                        logger.error(
                            f"Final REST API attempt also failed: {str(final_error)}"
                        )
                time.sleep(2)  # Increased wait time between retries

        raise ConnectionError(
            f"Failed to connect to WordPress site {self.url} after all attempts"
        )

    def create_post(
        self,
        title: str,
        content: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Create a new WordPress post with memory optimization"""
        try:
            # Initialize connection if needed
            self._init_connection()

            if not categories and self.category:
                categories = [self.category]

            if self.use_rest_api:
                # Use REST API with memory optimization
                data = {"title": title, "content": content, "status": "publish"}

                if categories:
                    try:
                        # Get category IDs with memory optimization
                        cat_response = self.session.get(
                            f"{self.url}/wp-json/wp/v2/categories",
                            auth=(self.username, self.password),
                            timeout=self.timeout,
                            verify=False,
                        )
                        if cat_response.status_code == 200:
                            cat_list = cat_response.json()
                            cat_ids = [
                                cat["id"]
                                for cat in cat_list
                                if cat["name"] in categories
                            ]
                            if cat_ids:
                                data["categories"] = cat_ids
                    except Exception as e:
                        logger.error(f"Error getting categories: {str(e)}")

                try:
                    response = self.session.post(
                        f"{self.url}/wp-json/wp/v2/posts",
                        auth=(self.username, self.password),
                        json=data,
                        timeout=self.timeout,
                        verify=False,
                    )

                    if response.status_code in [201, 200]:
                        logger.info(
                            f"Successfully created post '{title}' using REST API"
                        )
                        return True
                    else:
                        logger.error(
                            f"Failed to create post using REST API: {response.status_code} - {response.text}"
                        )
                        return False
                finally:
                    # Clean up response
                    if "response" in locals():
                        response.close()

            else:
                # Use XML-RPC with memory optimization
                try:
                    post = WordPressPost()
                    post.title = title
                    post.content = content
                    post.terms_names = {
                        "category": categories or [],
                        "post_tag": tags or [],
                    }
                    post.post_status = "publish"

                    post_id = self.client.call(posts.NewPost(post))
                    logger.info(
                        f"Successfully created post '{title}' with ID {post_id}"
                    )
                    return True
                except Exception as e:
                    logger.error(f"XML-RPC post creation failed: {str(e)}")
                    # Try REST API as fallback
                    self.use_rest_api = True
                    logger.info("Switching to REST API for post creation")
                    return self.create_post(title, content, categories, tags)

        except Exception as e:
            logger.error(f"Error creating post '{title}': {str(e)}")
            # Try to reconnect
            try:
                self._init_connection()
                logger.info("Reconnected successfully, retrying post creation")
                return self.create_post(title, content, categories, tags)
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect and retry: {str(reconnect_error)}")
                return False

    def test_connection(self) -> bool:
        """Test the connection to WordPress site with memory optimization"""
        try:
            # Initialize connection if needed
            self._init_connection()

            if self.use_rest_api:
                try:
                    response = self.session.get(
                        f"{self.url}/wp-json/wp/v2/posts",
                        auth=(self.username, self.password),
                        timeout=self.timeout,
                        verify=False,
                    )
                    result = response.status_code == 200
                    response.close()
                    return result
                except Exception as e:
                    logger.error(f"REST API test failed: {str(e)}")
                    return False
            else:
                try:
                    self.client.call(posts.GetPosts({"number": 1}))
                    return True
                except Exception as e:
                    logger.error(f"XML-RPC test failed: {str(e)}")
                    # Try REST API as fallback
                    self.use_rest_api = True
                    return self.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def __del__(self):
        """Cleanup resources"""
        if self._session:
            self._session.close()
            self._session = None


class PinterestIntegration:
    """Handles Pinterest integration for content sharing with optimized memory management"""

    def __init__(
        self,
        access_token: str,
        email: str = None,
        password: str = None,
        default_board: str = None,
        avoid_spam: dict = None,
    ):
        """Initialize Pinterest integration with memory optimization"""
        self.access_token = access_token
        self.email = email
        self.password = password
        self.default_board = default_board
        self.avoid_spam = avoid_spam or {}
        self.api_url = "https://api.pinterest.com/v5"
        self._session = None
        self._headers = None
        self._last_request_time = 0
        self._request_cache_time = 60  # 1 minute cache

    @property
    def headers(self):
        """Lazy initialization of headers"""
        if self._headers is None:
            self._headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        return self._headers

    @property
    def session(self):
        """Lazy initialization of session"""
        if self._session is None:
            self._session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session

    def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        image_url: str,
        link: Optional[str] = None,
    ) -> Dict:
        """Create a new Pinterest pin with memory optimization"""
        try:
            endpoint = f"{self.api_url}/pins"
            data = {
                "board_id": board_id,
                "title": title,
                "description": description,
                "media_source": {"source_type": "image_url", "url": image_url},
            }
            if link:
                data["link"] = link

            try:
                response = self.session.post(endpoint, headers=self.headers, json=data)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Created Pinterest pin: {result.get('id')}")
                return result
            finally:
                if "response" in locals():
                    response.close()

        except Exception as e:
            logger.error(f"Error creating Pinterest pin: {e}")
            raise

    def get_boards(self) -> List[Dict]:
        """Get list of Pinterest boards with memory optimization"""
        try:
            endpoint = f"{self.api_url}/boards"
            try:
                response = self.session.get(endpoint, headers=self.headers)
                response.raise_for_status()
                return response.json().get("items", [])
            finally:
                if "response" in locals():
                    response.close()

        except Exception as e:
            logger.error(f"Error fetching Pinterest boards: {e}")
            raise

    def schedule_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        image_url: str,
        scheduled_time: datetime,
        link: Optional[str] = None,
    ) -> Dict:
        """Schedule a pin for future publishing with memory optimization"""
        try:
            endpoint = f"{self.api_url}/pins"
            data = {
                "board_id": board_id,
                "title": title,
                "description": description,
                "media_source": {"source_type": "image_url", "url": image_url},
                "scheduled_time": scheduled_time.isoformat(),
            }
            if link:
                data["link"] = link

            try:
                response = self.session.post(endpoint, headers=self.headers, json=data)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Scheduled Pinterest pin for {scheduled_time}")
                return result
            finally:
                if "response" in locals():
                    response.close()

        except Exception as e:
            logger.error(f"Error scheduling Pinterest pin: {e}")
            raise

    def __del__(self):
        """Cleanup resources"""
        if self._session:
            self._session.close()
            self._session = None


class ContentGenerator:
    """Handles content generation for WordPress and Pinterest with optimized memory management"""

    def __init__(self, openai_api_key: str):
        """Initialize content generator with memory optimization"""
        self.openai_api_key = openai_api_key
        self._headers = None
        self._session = None
        self._last_request_time = 0
        self._request_cache_time = 60  # 1 minute cache

    @property
    def headers(self):
        """Lazy initialization of headers"""
        if self._headers is None:
            self._headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }
        return self._headers

    @property
    def session(self):
        """Lazy initialization of session"""
        if self._session is None:
            self._session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session

    def generate_article(
        self, topic: str, keywords: List[str], length: str = "medium"
    ) -> Dict:
        """Generate an article using OpenAI with memory optimization"""
        try:
            # Implementation will use OpenAI API to generate content
            # This is a placeholder for the actual implementation
            pass

        except Exception as e:
            logger.error(f"Error generating article: {e}")
            raise

    def generate_image(
        self, prompt: str, size: str = "1024x1024", style: str = "natural"
    ) -> str:
        """Generate an image using OpenAI with memory optimization"""
        try:
            # Implementation will use OpenAI API to generate images
            # This is a placeholder for the actual implementation
            pass

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise

    def optimize_content(
        self, content: str, platform: str, target_keywords: List[str]
    ) -> str:
        """Optimize content for specific platform and keywords with memory optimization"""
        try:
            # Implementation will optimize content for SEO
            # This is a placeholder for the actual implementation
            pass

        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            raise

    def __del__(self):
        """Cleanup resources"""
        if self._session:
            self._session.close()
            self._session = None
