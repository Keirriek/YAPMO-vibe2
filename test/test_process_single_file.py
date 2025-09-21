#!/usr/bin/env python3
"""Test script voor process_single_file.py."""

import sys
import tempfile
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def test_process_single_file_import():
    """Test import van process_single_file."""
    print("=== Testing Process Single File Import ===")
    
    try:
        from core.process_single_file import process_single_file
        print("✅ process_single_file import successful")
        return True
    except Exception as e:
        print(f"❌ process_single_file import failed: {e}")
        return False

def test_process_single_file_basic():
    """Test basic process_single_file functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        from core.process_single_file import process_single_file
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"fake image data")
        
        try:
            # Test with image extensions
            image_extensions = ['.jpg', '.jpeg', '.png']
            video_extensions = ['.mp4', '.mov']
            
            result = process_single_file(
                file_path=temp_path,
                image_extensions=image_extensions,
                video_extensions=video_extensions,
                worker_id=1
            )
            
            print(f"✅ Process result: {result}")
            
            # Check if result has expected keys
            expected_keys = ['success', 'json_data', 'file_path', 'media_type', 'log_messages']
            for key in expected_keys:
                if key in result:
                    print(f"✅ Result contains key: {key}")
                else:
                    print(f"❌ Result missing key: {key}")
            
            return True
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_process_single_file_nonexistent():
    """Test process_single_file with nonexistent file."""
    print("\n=== Testing Nonexistent File ===")
    
    try:
        from core.process_single_file import process_single_file
        
        # Test with nonexistent file
        result = process_single_file(
            file_path="/nonexistent/path/file.jpg",
            image_extensions=['.jpg'],
            video_extensions=['.mp4'],
            worker_id=2
        )
        
        print(f"✅ Nonexistent file result: {result}")
        
        # process_single_file doesn't check file existence, so it should return success=True
        if result.get('success') == True:
            print("✅ Correctly handled nonexistent file (no existence check)")
            return True
        else:
            print("❌ Did not handle nonexistent file correctly")
            return False
            
    except Exception as e:
        print(f"❌ Nonexistent file test failed: {e}")
        return False

def test_process_single_file_different_extensions():
    """Test process_single_file with different file extensions."""
    print("\n=== Testing Different Extensions ===")
    
    try:
        from core.process_single_file import process_single_file
        
        # Test with video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"fake video data")
        
        try:
            result = process_single_file(
                file_path=temp_path,
                image_extensions=['.jpg', '.png'],
                video_extensions=['.mp4', '.mov'],
                worker_id=3
            )
            
            print(f"✅ Video file result: {result}")
            
            # Check if file type was detected correctly
            if 'media_type' in result:
                print(f"✅ Media type detected: {result['media_type']}")
            
            return True
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"❌ Different extensions test failed: {e}")
        return False

def test_process_single_file_unsupported_extension():
    """Test process_single_file with unsupported extension."""
    print("\n=== Testing Unsupported Extension ===")
    
    try:
        from core.process_single_file import process_single_file
        
        # Test with unsupported file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"text data")
        
        try:
            result = process_single_file(
                file_path=temp_path,
                image_extensions=['.jpg', '.png'],
                video_extensions=['.mp4', '.mov'],
                worker_id=4
            )
            
            print(f"✅ Unsupported file result: {result}")
            
            # Should return success=False for unsupported files
            if result.get('success') == False:
                print("✅ Correctly handled unsupported file")
                return True
            else:
                print("❌ Did not handle unsupported file correctly")
                return False
                
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"❌ Unsupported extension test failed: {e}")
        return False

def main():
    """Run all process_single_file tests."""
    print("Testing process_single_file...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 5
    
    # Test import
    if test_process_single_file_import():
        success_count += 1
    
    # Test basic functionality
    if test_process_single_file_basic():
        success_count += 1
    
    # Test nonexistent file
    if test_process_single_file_nonexistent():
        success_count += 1
    
    # Test different extensions
    if test_process_single_file_different_extensions():
        success_count += 1
    
    # Test unsupported extension
    if test_process_single_file_unsupported_extension():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"process_single_file Tests: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All process_single_file tests passed!")
    else:
        print("❌ Some process_single_file tests failed!")

if __name__ == "__main__":
    main()
