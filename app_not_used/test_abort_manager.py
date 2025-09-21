"""Unit tests voor AbortManager."""

import time
from unittest.mock import Mock

from managers.abort_manager import AbortManager
from queues.logging_queue import LoggingQueue, LogLevel
from queues.result_queue import ResultQueue


def test_abort_manager_initialization():
    """Test AbortManager initialization."""
    # Create mock components
    mock_result_queue = Mock(spec=ResultQueue)
    mock_logging_queue = Mock(spec=LoggingQueue)
    mock_database_manager = Mock()
    mock_logging_manager = Mock()
    
    # Create AbortManager
    abort_manager = AbortManager(
        mock_result_queue, 
        mock_logging_queue, 
        mock_database_manager, 
        mock_logging_manager
    )
    
    assert not abort_manager.is_abort_active()
    assert abort_manager.get_abort_info() == (None, None)


def test_abort_manager_abort():
    """Test abort functionality."""
    # Create mock components
    mock_result_queue = Mock(spec=ResultQueue)
    mock_logging_queue = Mock(spec=LoggingQueue)
    mock_database_manager = Mock()
    mock_logging_manager = Mock()
    
    # Create AbortManager
    abort_manager = AbortManager(
        mock_result_queue, 
        mock_logging_queue, 
        mock_database_manager, 
        mock_logging_manager
    )
    
    # Test abort
    abort_manager.abort("UI", "User clicked abort button")
    
    # Verify abort state
    assert abort_manager.is_abort_active()
    source, reason = abort_manager.get_abort_info()
    assert source == "UI"
    assert reason == "User clicked abort button"
    
    # Verify queue abort calls
    mock_result_queue.set_abort.assert_called_once()
    mock_logging_queue.set_abort.assert_called_once()
    
    # Verify logging call
    mock_logging_queue.put_log.assert_called_once()


def test_abort_manager_double_abort():
    """Test that double abort is ignored."""
    # Create mock components
    mock_result_queue = Mock(spec=ResultQueue)
    mock_logging_queue = Mock(spec=LoggingQueue)
    mock_database_manager = Mock()
    mock_logging_manager = Mock()
    
    # Create AbortManager
    abort_manager = AbortManager(
        mock_result_queue, 
        mock_logging_queue, 
        mock_database_manager, 
        mock_logging_manager
    )
    
    # First abort
    abort_manager.abort("UI", "First abort")
    assert abort_manager.is_abort_active()
    
    # Second abort (should be ignored)
    abort_manager.abort("ERROR", "Second abort")
    assert abort_manager.is_abort_active()
    
    # Verify only first abort was processed
    source, reason = abort_manager.get_abort_info()
    assert source == "UI"
    assert reason == "First abort"
    
    # Verify queues were only called once
    mock_result_queue.set_abort.assert_called_once()
    mock_logging_queue.set_abort.assert_called_once()


def test_abort_manager_reset():
    """Test abort reset functionality."""
    # Create mock components
    mock_result_queue = Mock(spec=ResultQueue)
    mock_logging_queue = Mock(spec=LoggingQueue)
    mock_database_manager = Mock()
    mock_logging_manager = Mock()
    
    # Create AbortManager
    abort_manager = AbortManager(
        mock_result_queue, 
        mock_logging_queue, 
        mock_database_manager, 
        mock_logging_manager
    )
    
    # Abort
    abort_manager.abort("UI", "Test abort")
    assert abort_manager.is_abort_active()
    
    # Reset
    abort_manager.reset_abort()
    assert not abort_manager.is_abort_active()
    assert abort_manager.get_abort_info() == (None, None)


def test_abort_manager_manager_stop():
    """Test manager stop functionality."""
    # Create mock components with stop method
    mock_result_queue = Mock(spec=ResultQueue)
    mock_logging_queue = Mock(spec=LoggingQueue)
    mock_database_manager = Mock()
    mock_database_manager.stop = Mock()
    mock_logging_manager = Mock()
    mock_logging_manager.stop = Mock()
    
    # Create AbortManager
    abort_manager = AbortManager(
        mock_result_queue, 
        mock_logging_queue, 
        mock_database_manager, 
        mock_logging_manager
    )
    
    # Abort
    abort_manager.abort("UI", "Test abort")
    
    # Verify stop methods were called
    mock_database_manager.stop.assert_called_once()
    mock_logging_manager.stop.assert_called_once()


def test_abort_manager_manager_close():
    """Test manager close functionality."""
    # Create mock components with close method
    mock_result_queue = Mock(spec=ResultQueue)
    mock_logging_queue = Mock(spec=LoggingQueue)
    mock_database_manager = Mock()
    mock_database_manager.close = Mock()
    mock_logging_manager = Mock()
    mock_logging_manager.close = Mock()
    
    # Create AbortManager
    abort_manager = AbortManager(
        mock_result_queue, 
        mock_logging_queue, 
        mock_database_manager, 
        mock_logging_manager
    )
    
    # Abort
    abort_manager.abort("UI", "Test abort")
    
    # Verify close methods were called
    mock_database_manager.close.assert_called_once()
    mock_logging_manager.close.assert_called_once()


if __name__ == "__main__":
    print("Running AbortManager unit tests...")
    
    test_abort_manager_initialization()
    print("✓ AbortManager initialization test passed")
    
    test_abort_manager_abort()
    print("✓ AbortManager abort test passed")
    
    test_abort_manager_double_abort()
    print("✓ AbortManager double abort test passed")
    
    test_abort_manager_reset()
    print("✓ AbortManager reset test passed")
    
    test_abort_manager_manager_stop()
    print("✓ AbortManager manager stop test passed")
    
    test_abort_manager_manager_close()
    print("✓ AbortManager manager close test passed")
    
    print("All tests passed! ✅")
