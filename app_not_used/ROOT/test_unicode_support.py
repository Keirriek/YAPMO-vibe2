#YAPMO_V3.0
"""Test script for Unicode support in file processing."""

import sys
import os
import tempfile
import time
sys.path.append('/workspaces/app')

from core.directory_processor import DirectoryProcessor

def create_unicode_test_directory():
    """Create a test directory with Unicode file names."""
    test_dir = tempfile.mkdtemp(prefix="yapmo_unicode_test_")
    
    # Create subdirectories with Unicode names
    unicode_dirs = [
        "images_测试",  # Chinese characters
        "videos_тест",  # Cyrillic characters
        "photos_テスト",  # Japanese characters
        "media_اختبار"  # Arabic characters
    ]
    
    for dir_name in unicode_dirs:
        os.makedirs(os.path.join(test_dir, dir_name), exist_ok=True)
    
    # Create test files with Unicode names
    unicode_files = [
        ("images_测试", "测试图片.jpg"),
        ("images_测试", "测试图像.png"),
        ("videos_тест", "тестовое_видео.mp4"),
        ("videos_тест", "тест_видео.avi"),
        ("photos_テスト", "テスト写真.gif"),
        ("photos_テスト", "テスト画像.bmp"),
        ("media_اختبار", "اختبار_صورة.jpg"),
        ("media_اختبار", "اختبار_فيديو.mp4")
    ]
    
    for subdir, filename in unicode_files:
        file_path = os.path.join(test_dir, subdir, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Test content for {filename}")
            print(f"Created: {file_path}")
        except Exception as e:
            print(f"Error creating {file_path}: {e}")
    
    return test_dir

def progress_callback(event_type: str, data):
    """Test progress callback."""
    if event_type == 'directory_processed':
        print(f"  - Directory processed: {data}")
    elif event_type == 'file_processed':
        print(f"  - File processed: {data}")

def test_unicode_support():
    """Test Unicode support in file processing."""
    
    print("Testing Unicode support...")
    print("=" * 50)
    
    # Create test directory with Unicode names
    test_dir = create_unicode_test_directory()
    print(f"Created Unicode test directory: {test_dir}")
    
    # Test data
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    # Create directory processor
    processor = DirectoryProcessor(max_workers=2, progress_callback=progress_callback)
    
    print("Created DirectoryProcessor")
    
    # Process directory
    print(f"\nProcessing Unicode directory: {test_dir}")
    result = processor.process_directory(test_dir, image_extensions, video_extensions)
    
    # Check result
    if result.get('success', False):
        print("✓ Unicode directory processing completed successfully")
        stats = result.get('stats', {})
        print(f"Statistics: {stats}")
        
        # Verify statistics
        expected_files = 8  # 4 images + 4 videos
        if stats.get('total_files') == expected_files:
            print(f"✓ Total files correct: {stats['total_files']}")
        else:
            print(f"✗ Total files incorrect: expected {expected_files}, got {stats.get('total_files')}")
        
        if stats.get('successful_files') == expected_files:
            print(f"✓ Successful files correct: {stats['successful_files']}")
        else:
            print(f"✗ Successful files incorrect: expected {expected_files}, got {stats.get('successful_files')}")
        
        if stats.get('directories_scanned') >= 4:  # At least 4 subdirectories
            print(f"✓ Directories scanned correct: {stats['directories_scanned']}")
        else:
            print(f"✗ Directories scanned incorrect: got {stats.get('directories_scanned')}")
        
    else:
        print(f"✗ Unicode directory processing failed: {result.get('error', 'Unknown error')}")
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(test_dir)
        print(f"\nCleaned up Unicode test directory: {test_dir}")
    except Exception as e:
        print(f"Error cleaning up: {e}")
    
    print("\n" + "=" * 50)
    print("Unicode support test completed!")

if __name__ == "__main__":
    test_unicode_support()
