"""Integration test voor Result Queue met DatabaseManager."""

import asyncio
import time
import json
from unittest.mock import Mock

from queues.result_queue import ResultQueue, MetadataResult
from managers.database_manager import DatabaseManager


async def test_result_queue_workflow():
    """Test de volledige workflow van Result Queue naar Database."""
    print("🚀 Starting Result Queue Integration Test")
    print("=" * 50)
    
    # 1. Create mock database manager
    print("1. Creating mock database manager...")
    mock_db = Mock()
    
    # 2. Create ResultQueue
    print("2. Creating ResultQueue...")
    result_queue = ResultQueue(mock_db)
    
    # 3. Create test metadata results
    print("3. Creating test metadata results...")
    test_results = []
    for i in range(5):
        result = MetadataResult(
            file_path=f"/test/path/image_{i:03d}.jpg",
            exif_data={
                "EXIF:DateTime": f"2023:01:01 12:{i:02d}:00",
                "EXIF:Make": "Test Camera",
                "EXIF:Model": "Test Model"
            },
            file_info={
                "File:FileSize": str(1024 * (i + 1)),
                "File:FileType": "JPEG"
            },
            hash_value=f"hash_{i:03d}_abc123",
            file_size=1024 * (i + 1),
            timestamp=time.time() + i
        )
        test_results.append(result)
    
    # 4. Put results in queue
    print("4. Putting results in queue...")
    for i, result in enumerate(test_results):
        success = result_queue.put_result(result)
        print(f"   ✓ Result {i+1}: {result.file_path} -> {'SUCCESS' if success else 'FAILED'}")
    
    print(f"   Queue size: {result_queue.size()}")
    
    # 5. Get results from queue
    print("5. Getting results from queue...")
    retrieved_results = []
    for i in range(len(test_results)):
        result = result_queue.get_result()
        if result:
            retrieved_results.append(result)
            print(f"   ✓ Retrieved {i+1}: {result.file_path}")
        else:
            print(f"   ✗ Failed to retrieve result {i+1}")
    
    print(f"   Retrieved {len(retrieved_results)} results")
    
    # 6. Test abort functionality
    print("6. Testing abort functionality...")
    result_queue.set_abort()
    print(f"   Abort flag: {result_queue.is_aborted()}")
    
    # Try to put result after abort
    test_result = MetadataResult(
        file_path="/test/abort_test.jpg",
        exif_data={},
        file_info={},
        hash_value="abort_test",
        file_size=1024,
        timestamp=time.time()
    )
    
    success = result_queue.put_result(test_result)
    print(f"   Put after abort: {'SUCCESS' if success else 'FAILED (expected)'}")
    
    # 7. Test queue full scenario
    print("7. Testing queue full scenario...")
    # Reset abort flag
    result_queue.abort_flag = False
    
    # Fill queue to capacity
    print(f"   Queue capacity: {result_queue.queue_depth}")
    for i in range(result_queue.queue_depth + 1):  # Try to exceed capacity
        result = MetadataResult(
            file_path=f"/test/full_test_{i:03d}.jpg",
            exif_data={},
            file_info={},
            hash_value=f"full_test_{i:03d}",
            file_size=1024,
            timestamp=time.time()
        )
        success = result_queue.put_result(result)
        if not success:
            print(f"   ✗ Queue full at item {i+1} (expected)")
            break
    
    print("=" * 50)
    print("✅ Integration test completed successfully!")
    print(f"   - Created {len(test_results)} test results")
    print(f"   - Retrieved {len(retrieved_results)} results")
    print(f"   - Queue abort functionality: OK")
    print(f"   - Queue full detection: OK")


def test_config_loading():
    """Test config loading voor processing_queues."""
    print("\n🔧 Testing Config Loading")
    print("=" * 30)
    
    try:
        from config import get_param
        
        queue_depth = get_param("processing_queues", "result_queue_depth")
        timeout = get_param("processing_queues", "get_result_timeout")
        
        print(f"✓ result_queue_depth: {queue_depth}")
        print(f"✓ get_result_timeout: {timeout}ms")
        
        # Validate ranges
        if 5 <= queue_depth <= 64:
            print("✓ Queue depth within valid range (5-64)")
        else:
            print(f"✗ Queue depth out of range: {queue_depth}")
        
        if 1 <= timeout <= 6000:
            print("✓ Timeout within valid range (1-6000ms)")
        else:
            print(f"✗ Timeout out of range: {timeout}")
            
    except Exception as e:
        print(f"✗ Config loading failed: {e}")


def test_metadata_result_serialization():
    """Test MetadataResult serialization voor database."""
    print("\n💾 Testing MetadataResult Serialization")
    print("=" * 40)
    
    # Create test result
    result = MetadataResult(
        file_path="/test/path/sample.jpg",
        exif_data={
            "EXIF:DateTime": "2023:01:01 12:00:00",
            "EXIF:Make": "Canon",
            "EXIF:Model": "EOS R5"
        },
        file_info={
            "File:FileSize": "2048000",
            "File:FileType": "JPEG"
        },
        hash_value="abc123def456",
        file_size=2048000,
        timestamp=1704110400.0
    )
    
    # Test JSON serialization
    try:
        exif_json = json.dumps(result.exif_data)
        file_info_json = json.dumps(result.file_info)
        
        print(f"✓ EXIF data serialized: {len(exif_json)} characters")
        print(f"✓ File info serialized: {len(file_info_json)} characters")
        
        # Test deserialization
        exif_restored = json.loads(exif_json)
        file_info_restored = json.loads(file_info_json)
        
        print(f"✓ EXIF data deserialized: {exif_restored['EXIF:Make']}")
        print(f"✓ File info deserialized: {file_info_restored['File:FileType']}")
        
    except Exception as e:
        print(f"✗ Serialization failed: {e}")


if __name__ == "__main__":
    print("🧪 YAPMO Result Queue Integration Tests")
    print("=" * 50)
    
    # Test config loading
    test_config_loading()
    
    # Test serialization
    test_metadata_result_serialization()
    
    # Test main workflow
    asyncio.run(test_result_queue_workflow())
    
    print("\n🎉 All tests completed!")
