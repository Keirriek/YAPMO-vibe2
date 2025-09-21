"""Unit tests voor ResultQueue."""

import time
import asyncio
from unittest.mock import Mock

from queues.result_queue import ResultQueue, MetadataResult


def test_metadata_result_creation():
    """Test MetadataResult dataclass creation."""
    result = MetadataResult(
        file_path="/test/path/image.jpg",
        exif_data={"EXIF:DateTime": "2023:01:01 12:00:00"},
        file_info={"File:FileSize": "1024"},
        hash_value="abc123",
        file_size=1024,
        timestamp=time.time()
    )
    
    assert result.file_path == "/test/path/image.jpg"
    assert result.exif_data["EXIF:DateTime"] == "2023:01:01 12:00:00"
    assert result.hash_value == "abc123"
    assert result.file_size == 1024


def test_result_queue_initialization():
    """Test ResultQueue initialization."""
    mock_db = Mock()
    queue = ResultQueue(mock_db)
    
    assert queue.database_manager == mock_db
    assert queue.queue_depth == 32  # Default from config
    assert queue.get_timeout == 0.5  # 500ms converted to seconds
    assert not queue.is_aborted()
    assert queue.is_empty()
    assert not queue.is_full()


def test_result_queue_put_get():
    """Test putting and getting results from queue."""
    mock_db = Mock()
    queue = ResultQueue(mock_db)
    
    # Create test result
    result = MetadataResult(
        file_path="/test/path/image.jpg",
        exif_data={"EXIF:DateTime": "2023:01:01 12:00:00"},
        file_info={"File:FileSize": "1024"},
        hash_value="abc123",
        file_size=1024,
        timestamp=time.time()
    )
    
    # Put result
    success = queue.put_result(result)
    assert success is True
    assert queue.size() == 1
    assert not queue.is_empty()
    
    # Get result
    retrieved = queue.get_result()
    assert retrieved is not None
    assert retrieved.file_path == result.file_path
    assert retrieved.hash_value == result.hash_value
    assert queue.is_empty()


def test_result_queue_abort():
    """Test abort functionality."""
    mock_db = Mock()
    queue = ResultQueue(mock_db)
    
    # Create test result
    result = MetadataResult(
        file_path="/test/path/image.jpg",
        exif_data={},
        file_info={},
        hash_value="abc123",
        file_size=1024,
        timestamp=time.time()
    )
    
    # Put result
    queue.put_result(result)
    assert queue.size() == 1
    
    # Abort
    queue.set_abort()
    assert queue.is_aborted()
    
    # Try to put another result (should fail)
    success = queue.put_result(result)
    assert success is False
    
    # Try to get result (should return None)
    retrieved = queue.get_result()
    assert retrieved is None


def test_result_queue_timeout():
    """Test queue timeout behavior."""
    mock_db = Mock()
    queue = ResultQueue(mock_db)
    
    # Try to get from empty queue (should timeout and return None)
    start_time = time.time()
    result = queue.get_result()
    end_time = time.time()
    
    assert result is None
    assert (end_time - start_time) >= 0.4  # Should be close to 0.5s timeout


if __name__ == "__main__":
    print("Running ResultQueue unit tests...")
    
    test_metadata_result_creation()
    print("✓ MetadataResult creation test passed")
    
    test_result_queue_initialization()
    print("✓ ResultQueue initialization test passed")
    
    test_result_queue_put_get()
    print("✓ ResultQueue put/get test passed")
    
    test_result_queue_abort()
    print("✓ ResultQueue abort test passed")
    
    test_result_queue_timeout()
    print("✓ ResultQueue timeout test passed")
    
    print("All tests passed! ✅")
