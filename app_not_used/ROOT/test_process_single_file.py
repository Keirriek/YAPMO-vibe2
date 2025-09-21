#YAPMO_V3.0
"""Test script for process_single_file function."""

import sys
import os
sys.path.append('/workspaces/app')

from core.process_single_file import process_single_file

def test_process_single_file():
    """Test the process_single_file function."""
    
    # Test data
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    # Test cases
    test_cases = [
        {
            "file_path": "/test/images/sample.jpg",
            "expected_type": "image",
            "expected_success": True
        },
        {
            "file_path": "/test/videos/sample.mp4", 
            "expected_type": "video",
            "expected_success": True
        },
        {
            "file_path": "/test/documents/sample.txt",
            "expected_type": None,
            "expected_success": False
        }
    ]
    
    print("Testing process_single_file function...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['file_path']}")
        
        result = process_single_file(
            test_case['file_path'],
            image_extensions,
            video_extensions,
            worker_id=i
        )
        
        # Check success
        if result['success'] == test_case['expected_success']:
            print(f"✓ Success check: PASSED")
        else:
            print(f"✗ Success check: FAILED (expected {test_case['expected_success']}, got {result['success']})")
        
        # Check media type if successful
        if result['success'] and test_case['expected_type']:
            if result.get('media_type') == test_case['expected_type']:
                print(f"✓ Media type check: PASSED ({result['media_type']})")
            else:
                print(f"✗ Media type check: FAILED (expected {test_case['expected_type']}, got {result.get('media_type')})")
        
        # Check log messages
        if 'log_messages' in result and result['log_messages']:
            print(f"✓ Log messages: {len(result['log_messages'])} messages")
            for msg in result['log_messages']:
                print(f"  - {msg}")
        else:
            print("✗ Log messages: MISSING")
        
        # Check JSON data if successful
        if result['success'] and 'json_data' in result:
            json_data = result['json_data']
            print(f"✓ JSON data: {json_data}")
        elif not result['success']:
            print(f"✓ Error message: {result.get('error', 'No error message')}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_process_single_file()
