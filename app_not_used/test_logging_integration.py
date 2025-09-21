"""Integration test voor Logging Queue met LoggingManager."""

import asyncio
import time
from pathlib import Path

from queues.logging_queue import LoggingQueue, LogLevel
from managers.logging_manager import LoggingManager


async def test_logging_workflow():
    """Test de volledige logging workflow."""
    print("🚀 Starting Logging Integration Test")
    print("=" * 50)
    
    # 1. Create LoggingQueue
    print("1. Creating LoggingQueue...")
    logging_queue = LoggingQueue()
    
    # 2. Create LoggingManager
    print("2. Creating LoggingManager...")
    logging_manager = LoggingManager(logging_queue)
    
    # 3. Start logging consumer in background
    print("3. Starting logging consumer...")
    consumer_task = asyncio.create_task(logging_manager.start_consumer())
    
    # 4. Test different log levels
    print("4. Testing different log levels...")
    test_logs = [
        (LogLevel.INFO, "Application started successfully"),
        (LogLevel.NOTICE, "User selected directory: /test/path"),
        (LogLevel.WARNING, "File access denied: /test/readonly.jpg"),
        (LogLevel.ERROR, "Database connection failed"),
        (LogLevel.DEBUG, "Processing file: /test/image.jpg"),
        (LogLevel.EXTENDED, "Detailed metadata: EXIF:Make=Canon, EXIF:Model=EOS R5"),
    ]
    
    for level, message in test_logs:
        success = logging_queue.put_log(level, message)
        print(f"   ✓ {level.value}: {message} -> {'SUCCESS' if success else 'FAILED'}")
        await asyncio.sleep(0.1)  # Small delay to let consumer process
    
    # 5. Wait for all logs to be processed
    print("5. Waiting for logs to be processed...")
    await asyncio.sleep(1)
    
    # 6. Test abort functionality
    print("6. Testing abort functionality...")
    logging_queue.set_abort()
    print(f"   Abort flag: {logging_queue.is_aborted()}")
    
    # Try to put log after abort
    success = logging_queue.put_log(LogLevel.INFO, "This should fail")
    print(f"   Put after abort: {'SUCCESS' if success else 'FAILED (expected)'}")
    
    # 7. Stop consumer
    print("7. Stopping logging consumer...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    
    # 8. Check log files
    print("8. Checking log files...")
    log_file_path = Path("./logs/yapmo.log")
    debug_file_path = Path("./logs/debug.log")
    
    if log_file_path.exists():
        with open(log_file_path, 'r') as f:
            log_content = f.read()
            print(f"   ✓ Log file created: {len(log_content)} characters")
            print(f"   ✓ Log entries: {log_content.count('[')} entries")
    else:
        print("   ✗ Log file not found")
    
    if debug_file_path.exists():
        with open(debug_file_path, 'r') as f:
            debug_content = f.read()
            print(f"   ✓ Debug file created: {len(debug_content)} characters")
    else:
        print("   - Debug file not created (debug_mode=false)")
    
    print("=" * 50)
    print("✅ Logging integration test completed!")


def test_config_loading():
    """Test config loading voor logging parameters."""
    print("\n🔧 Testing Logging Config Loading")
    print("=" * 40)
    
    try:
        from config import get_param
        
        # Test logging config
        log_enabled = get_param("logging", "log_enabled")
        log_terminal = get_param("logging", "log_terminal")
        log_extended = get_param("logging", "log_extended")
        debug_mode = get_param("logging", "debug_mode")
        
        print(f"✓ log_enabled: {log_enabled}")
        print(f"✓ log_terminal: {log_terminal}")
        print(f"✓ log_extended: {log_extended}")
        print(f"✓ debug_mode: {debug_mode}")
        
        # Test queue config
        queue_depth = get_param("processing_queues", "logging_queue_depth")
        timeout = get_param("processing_queues", "get_log_timeout")
        
        print(f"✓ logging_queue_depth: {queue_depth}")
        print(f"✓ get_log_timeout: {timeout}ms")
        
    except Exception as e:
        print(f"✗ Config loading failed: {e}")


def test_log_level_filtering():
    """Test log level filtering logic."""
    print("\n🎯 Testing Log Level Filtering")
    print("=" * 35)
    
    try:
        from managers.logging_manager import LoggingManager
        from queues.logging_queue import LoggingQueue, LogLevel
        
        # Create test instances
        logging_queue = LoggingQueue()
        logging_manager = LoggingManager(logging_queue)
        
        # Test different scenarios
        test_cases = [
            (LogLevel.INFO, "Should be processed if log_enabled=true"),
            (LogLevel.NOTICE, "Should always be processed"),
            (LogLevel.WARNING, "Should always be processed"),
            (LogLevel.ERROR, "Should always be processed"),
            (LogLevel.DEBUG, "Should be processed if debug_mode=true"),
            (LogLevel.EXTENDED, "Should be processed if log_extended=true"),
        ]
        
        for level, description in test_cases:
            should_process = logging_manager._should_log_level(level)
            print(f"   {level.value}: {'✓' if should_process else '✗'} - {description}")
        
    except Exception as e:
        print(f"✗ Log level filtering test failed: {e}")


if __name__ == "__main__":
    print("🧪 YAPMO Logging Integration Tests")
    print("=" * 50)
    
    # Test config loading
    test_config_loading()
    
    # Test log level filtering
    test_log_level_filtering()
    
    # Test main workflow
    asyncio.run(test_logging_workflow())
    
    print("\n🎉 All logging tests completed!")
