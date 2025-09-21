#!/usr/bin/env python3
"""Test script voor logging_service_v2."""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.logging_service_v2 import logging_service
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic logging functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        # Test basic logging
        logging_service.log("INFO", "Test message")
        print("✅ Basic logging works")
    except Exception as e:
        print(f"❌ Basic logging failed: {e}")

def test_ui_messages():
    """Test UI message functionality."""
    print("\n=== Testing UI Messages ===")
    
    try:
        # Log some messages
        logging_service.log("INFO", "UI test message 1")
        logging_service.log("WARNING", "UI test message 2")
        
        # Get UI messages
        messages = logging_service.get_ui_messages()
        print(f"✅ Retrieved {len(messages)} UI messages")
        
        for i, msg in enumerate(messages):
            print(f"  Message {i+1}: [{msg['timestamp']}] {msg['level']}: {msg['message']}")
            
    except Exception as e:
        print(f"❌ UI messages test failed: {e}")

def test_file_creation():
    """Test log file creation."""
    print("\n=== Testing File Creation ===")
    
    try:
        log_file = Path("./log/yapmo_log.log")
        debug_file = Path("./log/yapmo_debug.log")
        
        print(f"Main log file exists: {log_file.exists()}")
        print(f"Debug log file exists: {debug_file.exists()}")
        
        if log_file.exists():
            print(f"Main log file size: {log_file.stat().st_size} bytes")
        if debug_file.exists():
            print(f"Debug log file size: {debug_file.stat().st_size} bytes")
            
        print("✅ File creation test completed")
        
    except Exception as e:
        print(f"❌ File creation test failed: {e}")

def main():
    """Run all tests."""
    print("Testing logging_service_v2...")
    
    test_basic_functionality()
    test_ui_messages()
    test_file_creation()
    
    print("\n=== Test Summary ===")
    print("Check the output above for any errors.")

if __name__ == "__main__":
    main()
