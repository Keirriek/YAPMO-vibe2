"""Unit tests voor LoggingQueue."""

import time
import asyncio
from unittest.mock import Mock

from queues.logging_queue import LoggingQueue, LogMessage, LogLevel


def test_log_level_enum():
    """Test LogLevel enum values."""
    assert LogLevel.INFO.value == "INFO"
    assert LogLevel.NOTICE.value == "NOTICE"
    assert LogLevel.ERROR.value == "ERROR"
    assert LogLevel.WARNING.value == "WARNING"
    assert LogLevel.DEBUG.value == "DEBUG"
    assert LogLevel.EXTENDED.value == "EXTENDED"


def test_log_message_creation():
    """Test LogMessage dataclass creation."""
    log_msg = LogMessage(
        timestamp=time.time(),
        level=LogLevel.INFO,
        message="Test log message"
    )
    
    assert log_msg.level == LogLevel.INFO
    assert log_msg.message == "Test log message"
    assert isinstance(log_msg.timestamp, float)


def test_logging_queue_initialization():
    """Test LoggingQueue initialization."""
    queue = LoggingQueue()
    
    assert queue.queue_depth == 200  # Default from config
    assert queue.get_timeout == 0.1  # 100ms converted to seconds
    assert not queue.is_aborted()
    assert queue.is_empty()
    assert not queue.is_full()


def test_logging_queue_put_get():
    """Test putting and getting logs from queue."""
    queue = LoggingQueue()
    
    # Create test log message
    log_msg = LogMessage(
        timestamp=time.time(),
        level=LogLevel.INFO,
        message="Test log message"
    )
    
    # Put log
    success = queue.put_log(LogLevel.INFO, "Test log message")
    assert success is True
    assert queue.size() == 1
    assert not queue.is_empty()
    
    # Get log
    retrieved = queue.get_log()
    assert retrieved is not None
    assert retrieved.level == LogLevel.INFO
    assert retrieved.message == "Test log message"
    assert queue.is_empty()


def test_logging_queue_abort():
    """Test abort functionality."""
    queue = LoggingQueue()
    
    # Put log
    queue.put_log(LogLevel.INFO, "Test message")
    assert queue.size() == 1
    
    # Abort
    queue.set_abort()
    assert queue.is_aborted()
    
    # Try to put another log (should fail)
    success = queue.put_log(LogLevel.WARNING, "Test warning")
    assert success is False
    
    # Try to get log (should return None)
    retrieved = queue.get_log()
    assert retrieved is None


def test_logging_queue_timeout():
    """Test queue timeout behavior."""
    queue = LoggingQueue()
    
    # Try to get from empty queue (should timeout and return None)
    start_time = time.time()
    log_msg = queue.get_log()
    end_time = time.time()
    
    assert log_msg is None
    assert (end_time - start_time) >= 0.05  # Should be close to 0.1s timeout


def test_logging_queue_error_reserved_space():
    """Test ERROR level reserved space functionality."""
    queue = LoggingQueue()
    
    # Fill queue to capacity (minus 1 for reserved space)
    for i in range(queue.queue_depth - 1):
        success = queue.put_log(LogLevel.INFO, f"Test message {i}")
        assert success is True
    
    # Queue should be full for non-ERROR levels
    success = queue.put_log(LogLevel.WARNING, "This should fail")
    assert success is False
    
    # But ERROR level should still work (reserved space)
    success = queue.put_log(LogLevel.ERROR, "This should work")
    assert success is True


if __name__ == "__main__":
    print("Running LoggingQueue unit tests...")
    
    test_log_level_enum()
    print("✓ LogLevel enum test passed")
    
    test_log_message_creation()
    print("✓ LogMessage creation test passed")
    
    test_logging_queue_initialization()
    print("✓ LoggingQueue initialization test passed")
    
    test_logging_queue_put_get()
    print("✓ LoggingQueue put/get test passed")
    
    test_logging_queue_abort()
    print("✓ LoggingQueue abort test passed")
    
    test_logging_queue_timeout()
    print("✓ LoggingQueue timeout test passed")
    
    test_logging_queue_error_reserved_space()
    print("✓ LoggingQueue ERROR reserved space test passed")
    
    print("All tests passed! ✅")
