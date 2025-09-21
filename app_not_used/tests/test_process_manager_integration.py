"""
Integration tests for ProcessManager
Stage 1.3: Process Manager Integration Testing
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from managers.process_manager import ProcessManager, TaskStatus, ConfigManager, QueueManager
from managers.abort_manager import AbortManager

class TestProcessManagerIntegration:
    """Integration tests for ProcessManager with other managers"""
    
    @pytest.fixture
    def real_managers(self):
        """Create real manager instances for integration testing"""
        # Create real ConfigManager
        config_manager = ConfigManager()
        config_manager.set('max_workers', 4)
        
        # Create real QueueManager
        queue_manager = QueueManager()
        
        # Create real AbortManager
        abort_manager = AbortManager()
        
        return config_manager, queue_manager, abort_manager
    
    @pytest.fixture
    def process_manager(self, real_managers):
        """Create ProcessManager with real managers"""
        config_manager, queue_manager, abort_manager = real_managers
        return ProcessManager(config_manager, queue_manager, abort_manager)
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, process_manager):
        """Test complete ProcessManager lifecycle"""
        # Start process manager
        await process_manager.start()
        assert process_manager.is_running()
        
        # Submit multiple tasks
        task_ids = []
        for i in range(3):
            def test_func():
                time.sleep(0.01)
                return f"result_{i}"
            
            task_id = await process_manager.submit_task(f"task_{i}", test_func, total_items=10)
            task_ids.append(task_id)
        
        # Wait for tasks to complete
        await asyncio.sleep(0.1)
        
        # Check all tasks completed
        for task_id in task_ids:
            task = process_manager.get_task_status(task_id)
            assert task.status == TaskStatus.COMPLETED
            assert task.result is not None
        
        # Stop process manager
        await process_manager.stop()
        assert not process_manager.is_running()
    
    @pytest.mark.asyncio
    async def test_abort_integration(self, process_manager):
        """Test abort integration with AbortManager"""
        await process_manager.start()
        
        # Submit long-running task
        def long_running_func():
            time.sleep(0.2)
            return "result"
        
        task_id = await process_manager.submit_task("long_task", long_running_func)
        
        # Wait a bit
        await asyncio.sleep(0.05)
        
        # Abort via AbortManager
        process_manager.abort_manager.abort()
        
        # Wait for abort to take effect
        await asyncio.sleep(0.1)
        
        # Check task was aborted
        task = process_manager.get_task_status(task_id)
        assert task.status == TaskStatus.ABORTED
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_queue_integration(self, process_manager):
        """Test queue integration for progress updates"""
        await process_manager.start()
        
        # Mock function that simulates progress
        def progress_func():
            time.sleep(0.01)
            return "result"
        
        # Submit task
        task_id = await process_manager.submit_task("progress_task", progress_func, total_items=5)
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        # Check progress updates were sent to queue
        # Note: In real implementation, we'd check the queue contents
        # For now, we just verify the task completed successfully
        task = process_manager.get_task_status(task_id)
        assert task.status == TaskStatus.COMPLETED
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_config_integration(self, process_manager):
        """Test config integration for max_workers"""
        # Check that max_workers is read from config
        assert process_manager.max_workers == 4
        
        # Test that worker pool respects the limit
        await process_manager.start()
        
        # Submit more tasks than max_workers
        task_ids = []
        for i in range(6):  # More than max_workers (4)
            def test_func():
                time.sleep(0.01)
                return f"result_{i}"
            
            task_id = await process_manager.submit_task(f"task_{i}", test_func)
            task_ids.append(task_id)
        
        # Wait for all tasks to complete
        await asyncio.sleep(0.2)
        
        # Check all tasks completed (worker pool should handle the limit)
        for task_id in task_ids:
            task = process_manager.get_task_status(task_id)
            assert task.status == TaskStatus.COMPLETED
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, process_manager):
        """Test error handling integration"""
        await process_manager.start()
        
        # Submit task that will fail
        def failing_func():
            raise ValueError("Integration test error")
        
        task_id = await process_manager.submit_task("failing_task", failing_func)
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        # Check task failed gracefully
        task = process_manager.get_task_status(task_id)
        assert task.status == TaskStatus.FAILED
        assert "Integration test error" in task.error
        
        # Check process manager is still running
        assert process_manager.is_running()
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_tasks(self, process_manager):
        """Test concurrent task execution"""
        await process_manager.start()
        
        # Submit multiple concurrent tasks
        task_ids = []
        for i in range(8):  # More than max_workers
            def test_func():
                time.sleep(0.01)
                return f"concurrent_result_{i}"
            
            task_id = await process_manager.submit_task(f"concurrent_task_{i}", test_func)
            task_ids.append(task_id)
        
        # Wait for all tasks to complete
        await asyncio.sleep(0.2)
        
        # Check all tasks completed
        for task_id in task_ids:
            task = process_manager.get_task_status(task_id)
            assert task.status == TaskStatus.COMPLETED
            assert task.result is not None
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_mixed_task_types(self, process_manager):
        """Test mixed sync and async tasks"""
        await process_manager.start()
        
        # Submit sync task
        def sync_func():
            time.sleep(0.01)
            return "sync_result"
        
        sync_task_id = await process_manager.submit_task("sync_task", sync_func)
        
        # Submit async task
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"
        
        async_task_id = await process_manager.submit_task("async_task", async_func)
        
        # Wait for both tasks to complete
        await asyncio.sleep(0.1)
        
        # Check both tasks completed
        sync_task = process_manager.get_task_status(sync_task_id)
        async_task = process_manager.get_task_status(async_task_id)
        
        assert sync_task.status == TaskStatus.COMPLETED
        assert sync_task.result == "sync_result"
        
        assert async_task.status == TaskStatus.COMPLETED
        assert async_task.result == "async_result"
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_worker_stats_integration(self, process_manager):
        """Test worker statistics integration"""
        await process_manager.start()
        
        # Check initial stats
        stats = process_manager.get_worker_stats()
        assert stats['max_workers'] == 4
        assert stats['total_tasks'] == 0
        assert stats['running_tasks'] == 0
        assert stats['completed_tasks'] == 0
        
        # Submit some tasks
        task_ids = []
        for i in range(3):
            def test_func():
                time.sleep(0.01)
                return f"result_{i}"
            
            task_id = await process_manager.submit_task(f"task_{i}", test_func)
            task_ids.append(task_id)
        
        # Wait for tasks to complete
        await asyncio.sleep(0.1)
        
        # Check updated stats
        stats = process_manager.get_worker_stats()
        assert stats['total_tasks'] == 3
        assert stats['completed_tasks'] == 3
        assert stats['running_tasks'] == 0
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_task_cleanup_integration(self, process_manager):
        """Test task cleanup integration"""
        await process_manager.start()
        
        # Submit and complete some tasks
        task_ids = []
        for i in range(3):
            def test_func():
                time.sleep(0.01)
                return f"result_{i}"
            
            task_id = await process_manager.submit_task(f"task_{i}", test_func)
            task_ids.append(task_id)
        
        # Wait for tasks to complete
        await asyncio.sleep(0.1)
        
        # Check tasks exist
        assert len(process_manager.get_all_tasks()) == 3
        
        # Clear completed tasks
        process_manager.clear_completed_tasks()
        
        # Check tasks were cleared
        assert len(process_manager.get_all_tasks()) == 0
        
        await process_manager.stop()
    
    @pytest.mark.asyncio
    async def test_restart_integration(self, process_manager):
        """Test restarting process manager"""
        # Start process manager
        await process_manager.start()
        assert process_manager.is_running()
        
        # Submit a task
        def test_func():
            return "result"
        
        task_id = await process_manager.submit_task("test_task", test_func)
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        # Stop process manager
        await process_manager.stop()
        assert not process_manager.is_running()
        
        # Start again
        await process_manager.start()
        assert process_manager.is_running()
        
        # Submit another task
        task_id2 = await process_manager.submit_task("test_task2", test_func)
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        
        # Check both tasks exist
        assert len(process_manager.get_all_tasks()) == 2
        
        await process_manager.stop()
