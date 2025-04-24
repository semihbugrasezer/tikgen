from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import datetime
import logging
from contextlib import contextmanager
import sqlite3
from typing import Optional, Dict, Any, List
import gc
import psutil
import threading
from queue import Queue
import time

logger = logging.getLogger(__name__)

Base = declarative_base()


class Pin(Base):
    """Pin model for storing Pinterest pin data"""

    __tablename__ = "pins"

    id = Column(Integer, primary_key=True)
    pin_id = Column(String, unique=True)
    title = Column(String)
    description = Column(String)
    url = Column(String)
    image_url = Column(String)
    content_type = Column(String)
    keywords = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    engagement_data = Column(JSON)
    is_published = Column(Boolean, default=False)


class DatabaseManager:
    """Enhanced database manager with connection pooling and memory optimization"""

    _instance = None
    _lock = threading.Lock()
    _session_factory = None
    _engine = None
    _connection_pool = None
    _max_connections = 20
    _connection_timeout = 30
    _cleanup_interval = 300  # 5 minutes
    _last_cleanup = time.time()
    _memory_threshold = 0.8  # 80% memory usage threshold

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def init(self, engine=None):
        """Initialize database manager with connection pooling"""
        if self._engine is None:
            if engine is None:
                engine = create_engine(
                    "sqlite:///app.db",
                    poolclass=QueuePool,
                    pool_size=self._max_connections,
                    max_overflow=10,
                    pool_timeout=self._connection_timeout,
                    pool_recycle=1800,
                )
            self._engine = engine
            self._session_factory = scoped_session(
                sessionmaker(
                    bind=self._engine,
                    expire_on_commit=False,
                    autocommit=False,
                    autoflush=False,
                )
            )

    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = None
        try:
            session = self._session_factory()
            yield session
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            if session:
                session.close()
            self._check_memory_usage()

    def _check_memory_usage(self):
        """Check memory usage and perform cleanup if necessary"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            memory_percent = psutil.Process().memory_percent()
            if memory_percent > self._memory_threshold:
                self._perform_cleanup()
            self._last_cleanup = current_time

    def _perform_cleanup(self):
        """Perform memory cleanup"""
        try:
            # Force garbage collection
            gc.collect()

            # Clear SQLAlchemy session cache
            if self._session_factory:
                self._session_factory.remove()

            # Clear connection pool
            if self._engine:
                self._engine.dispose()

            logger.info("Database cleanup performed")
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")

    def get_pins_by_status(self, status: str, limit: int = 100) -> List[Pin]:
        """Get pins by status with memory optimization"""
        with self.get_session() as session:
            return session.query(Pin).filter(Pin.status == status).limit(limit).all()

    def get_pending_pins(self, wordpress_site: str, limit: int = 10) -> List[Pin]:
        """Get pending pins for a specific WordPress site"""
        with self.get_session() as session:
            return (
                session.query(Pin)
                .filter(Pin.status == "pending", Pin.wordpress_site == wordpress_site)
                .limit(limit)
                .all()
            )

    def update_pin(self, pin: Pin) -> bool:
        """Update pin with error handling"""
        try:
            with self.get_session() as session:
                session.merge(pin)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating pin: {e}")
            return False

    def add_pin(self, pin: Pin) -> bool:
        """Add new pin with error handling"""
        try:
            with self.get_session() as session:
                session.add(pin)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding pin: {e}")
            return False

    def delete_pin(self, pin_id: int) -> bool:
        """Delete pin with error handling"""
        try:
            with self.get_session() as session:
                pin = session.query(Pin).filter(Pin.id == pin_id).first()
                if pin:
                    session.delete(pin)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting pin: {e}")
            return False

    def __del__(self):
        """Cleanup resources on deletion"""
        self._perform_cleanup()


# Create global database manager instance
db_manager = DatabaseManager()

# Create a Session class for direct session management
Session = scoped_session(sessionmaker(bind=db_manager._engine, expire_on_commit=False))

# Export these objects
__all__ = ["Session", "Pin", "DatabaseManager", "db_manager", "Base"]
