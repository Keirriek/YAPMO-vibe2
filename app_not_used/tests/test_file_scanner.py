"""
Unit tests for FileScanner
Stage 2.1: File Scanner Testing
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from managers.file_scanner import FileScanner, ScanResult, ScanProgress
from managers.abort_manager import AbortManager
from managers.queue_manager import QueueManager
from config import ConfigManager

class TestFileScanner:
    """Test FileScanner functionality"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager"""
        config = Mock(spec=ConfigManager)
        config.get_param.side_effect = lambda section, key, default=None: {
            ("extensions", "image_extensions"): [".jpg", ".jpeg", ".png"],
            ("extensions", "video_extensions"): [".mp4", ".mov"],
            ("extensions", "sidecar_extensions"): [".aae", ".xmp"],
            ("logging", "log_extended"): False
        }.get((section, key), default)
        return config
    
    @pytest.fixture
    def mock_queue_manager(self):
        """Mock QueueManager"""
        queue_manager = Mock(spec=QueueManager)
        queue_manager.put_log = AsyncMock(return_value=True)
        return queue_manager
    
    @pytest.fixture
    def mock_abort_manager(self):
        """Mock AbortManager"""
        abort_manager = Mock(spec=AbortManager)
        abort_manager.is_abort_active.return_value = False
        return abort_manager
    
    @pytest.fixture
    def file_scanner(self, mock_config_manager, mock_queue_manager, mock_abort_manager):
        """Create FileScanner instance"""
        return FileScanner(mock_config_manager, mock_queue_manager, mock_abort_manager)
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory with test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectories
            subdir1 = Path(temp_dir) / "subdir1"
            subdir2 = Path(temp_dir) / "subdir2"
            subdir1.mkdir()
            subdir2.mkdir()
            
            # Create test files
            (Path(temp_dir) / "image1.jpg").touch()
            (Path(temp_dir) / "image2.png").touch()
            (Path(temp_dir) / "video1.mp4").touch()
            (Path(temp_dir) / "sidecar1.aae").touch()
            (Path(temp_dir) / "other.txt").touch()
            
            (subdir1 / "image3.jpeg").touch()
            (subdir1 / "video2.mov").touch()
            (subdir1 / "sidecar2.xmp").touch()
            
            (subdir2 / "image4.jpg").touch()
            (subdir2 / "other2.doc").touch()
            
            yield temp_dir
    
    def test_file_scanner_initialization(self, file_scanner):
        """Test FileScanner initialization"""
        assert not file_scanner.scanning
        assert file_scanner.scan_start_time is None
        assert file_scanner.scan_path is None
        assert file_scanner.files_found == 0
        assert file_scanner.directories_scanned == 0
    
    @pytest.mark.asyncio
    async def test_scan_directory_success(self, file_scanner, temp_directory):
        """Test successful directory scanning"""
        result = await file_scanner.scan_directory(temp_directory)
        
        # Check result structure
        assert isinstance(result, ScanResult)
        assert result.scan_path == temp_directory
        assert result.scan_duration > 0
        
        # Check file counts
        assert result.total_files == 10  # All files (5 media + 2 sidecars + 3 other)
        assert result.media_files == 6  # 4 images + 2 videos
        assert result.sidecars == 2  # 2 sidecar files
        assert result.directories == 2  # 2 subdirectories
        
        # Check file list
        assert len(result.file_list) == 6  # Only media files
        assert all(f.endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov')) for f in result.file_list)
        
        # Check extension counts
        assert result.by_extension['.jpg'] == 2
        assert result.by_extension['.png'] == 1
        assert result.by_extension['.jpeg'] == 1
        assert result.by_extension['.mp4'] == 1
        assert result.by_extension['.mov'] == 1
        assert result.by_extension['.aae'] == 1
        assert result.by_extension['.xmp'] == 1
        assert result.by_extension['.txt'] == 1
        assert result.by_extension['.doc'] == 1
    
    @pytest.mark.asyncio
    async def test_scan_directory_not_exists(self, file_scanner):
        """Test scanning non-existent directory"""
        with pytest.raises(ValueError, match="Directory does not exist"):
            await file_scanner.scan_directory("/non/existent/path")
    
    @pytest.mark.asyncio
    async def test_scan_directory_not_directory(self, file_scanner, temp_directory):
        """Test scanning file instead of directory"""
        test_file = Path(temp_directory) / "test.txt"
        test_file.touch()
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            await file_scanner.scan_directory(str(test_file))
    
    @pytest.mark.asyncio
    async def test_scan_directory_already_scanning(self, file_scanner, temp_directory):
        """Test scanning when already scanning"""
        # Start a scan
        file_scanner.scanning = True
        
        with pytest.raises(RuntimeError, match="Scanner already running"):
            await file_scanner.scan_directory(temp_directory)
    
    @pytest.mark.asyncio
    async def test_scan_directory_abort(self, file_scanner, temp_directory, mock_abort_manager):
        """Test scan abort functionality"""
        # Mock abort after some time
        call_count = 0
        def mock_is_abort_active():
            nonlocal call_count
            call_count += 1
            return call_count > 10  # Abort after 10 calls
        
        mock_abort_manager.is_abort_active = mock_is_abort_active
        
        result = await file_scanner.scan_directory(temp_directory)
        
        # Should have found some files before abort
        assert result.total_files > 0
        assert result.total_files < 10  # Not all files due to abort
    
    @pytest.mark.asyncio
    async def test_scan_directory_progress_callback(self, file_scanner, temp_directory):
        """Test progress callback functionality"""
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        result = await file_scanner.scan_directory(temp_directory, progress_callback)
        
        # Should have received progress updates
        assert len(progress_updates) > 0
        assert all(isinstance(p, ScanProgress) for p in progress_updates)
        assert all(p.files_found > 0 for p in progress_updates)
    
    def test_is_scanning(self, file_scanner):
        """Test is_scanning method"""
        assert not file_scanner.is_scanning()
        
        file_scanner.scanning = True
        assert file_scanner.is_scanning()
        
        file_scanner.scanning = False
        assert not file_scanner.is_scanning()
    
    def test_get_scan_stats(self, file_scanner):
        """Test get_scan_stats method"""
        stats = file_scanner.get_scan_stats()
        
        assert stats['scanning'] == False
        assert stats['scan_path'] is None
        assert stats['files_found'] == 0
        assert stats['directories_scanned'] == 0
        assert stats['scan_duration'] == 0.0
        
        # Test with scanning state
        file_scanner.scanning = True
        file_scanner.scan_path = "/test/path"
        file_scanner.files_found = 100
        file_scanner.directories_scanned = 10
        file_scanner.scan_start_time = 1234567890.0
        
        with patch('time.time', return_value=1234567895.0):
            stats = file_scanner.get_scan_stats()
            
            assert stats['scanning'] == True
            assert stats['scan_path'] == "/test/path"
            assert stats['files_found'] == 100
            assert stats['directories_scanned'] == 10
            assert stats['scan_duration'] == 5.0
    
    def test_abort_scan(self, file_scanner):
        """Test abort_scan method"""
        # Should not raise error when not scanning
        file_scanner.abort_scan()
        
        # Should not raise error when scanning
        file_scanner.scanning = True
        file_scanner.abort_scan()

class TestScanResult:
    """Test ScanResult dataclass"""
    
    def test_scan_result_creation(self):
        """Test ScanResult creation"""
        result = ScanResult(
            total_files=100,
            media_files=50,
            sidecars=10,
            directories=5,
            by_extension={".jpg": 30, ".png": 20},
            file_list=["file1.jpg", "file2.png"],
            scan_duration=10.5,
            scan_path="/test/path"
        )
        
        assert result.total_files == 100
        assert result.media_files == 50
        assert result.sidecars == 10
        assert result.directories == 5
        assert result.by_extension[".jpg"] == 30
        assert result.by_extension[".png"] == 20
        assert len(result.file_list) == 2
        assert result.scan_duration == 10.5
        assert result.scan_path == "/test/path"

class TestScanProgress:
    """Test ScanProgress dataclass"""
    
    def test_scan_progress_creation(self):
        """Test ScanProgress creation"""
        progress = ScanProgress(
            current_directory="/test/dir",
            files_found=25,
            directories_scanned=5,
            progress_percentage=50.0,
            eta="2m 30s"
        )
        
        assert progress.current_directory == "/test/dir"
        assert progress.files_found == 25
        assert progress.directories_scanned == 5
        assert progress.progress_percentage == 50.0
        assert progress.eta == "2m 30s"
