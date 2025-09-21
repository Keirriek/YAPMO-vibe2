#!/usr/bin/env python3
"""
Working Memory Leak Test voor Fill Database V2

Test memory leaks met werkende imports
"""

import gc
import psutil
import sys
import time
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, '/workspaces')

def test_memory_basics() -> None:
    """Test basic memory monitoring."""
    print("🔍 Basic Memory Test")
    print("=" * 20)
    
    process = psutil.Process()
    
    # Test memory allocation patterns
    print(f"📊 Initial memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
    # Test 1: Simple data allocation
    print(f"\n🧪 Test 1: Simple data allocation")
    before = process.memory_info().rss / 1024 / 1024
    
    data = []
    for i in range(1000):
        data.append(f"Test string {i}" * 100)
    
    after = process.memory_info().rss / 1024 / 1024
    print(f"   Before: {before:.2f} MB")
    print(f"   After: {after:.2f} MB")
    print(f"   Diff: {after - before:.2f} MB")
    
    # Cleanup
    del data
    gc.collect()
    time.sleep(0.1)
    
    cleanup = process.memory_info().rss / 1024 / 1024
    print(f"   After cleanup: {cleanup:.2f} MB")
    print(f"   Cleanup diff: {cleanup - after:.2f} MB")
    
    # Test 2: Multiple cycles
    print(f"\n🧪 Test 2: Multiple allocation cycles")
    
    for cycle in range(5):
        before_cycle = process.memory_info().rss / 1024 / 1024
        
        # Allocate data
        cycle_data = []
        for i in range(500):
            cycle_data.append(f"Cycle {cycle} data {i}" * 50)
        
        after_cycle = process.memory_info().rss / 1024 / 1024
        
        # Cleanup
        del cycle_data
        gc.collect()
        time.sleep(0.1)
        
        final_cycle = process.memory_info().rss / 1024 / 1024
        
        print(f"   Cycle {cycle + 1}: {before_cycle:.2f} → {after_cycle:.2f} → {final_cycle:.2f} MB")
        
        # Check for leaks
        leak = final_cycle - before_cycle
        if leak > 1.0:  # More than 1MB leak
            print(f"   ⚠️  Potential leak: {leak:.2f} MB")
        else:
            print(f"   ✅ OK: {leak:.2f} MB")

def test_worker_simulation() -> None:
    """Simulate worker behavior without full app."""
    print(f"\n🔍 Worker Simulation Test")
    print("=" * 25)
    
    process = psutil.Process()
    
    # Simulate worker function
    def simulate_worker(file_path: str, worker_id: int) -> dict:
        """Simulate worker processing."""
        # Simulate work
        time.sleep(0.1)
        
        # Simulate result
        result = {
            'file_path': file_path,
            'worker_id': worker_id,
            'success': True,
            'processing_time': 0.1,
            'log_messages': [
                {'level': 'DEBUG', 'message': f'Worker {worker_id} processed {file_path}'}
            ]
        }
        return result
    
    # Test multiple workers
    print(f"🧪 Testing multiple worker simulations:")
    
    for cycle in range(3):
        before_cycle = process.memory_info().rss / 1024 / 1024
        
        # Simulate multiple workers
        results = []
        for i in range(10):
            result = simulate_worker(f"test_file_{i}.jpg", i)
            results.append(result)
        
        after_cycle = process.memory_info().rss / 1024 / 1024
        
        # Cleanup
        del results
        gc.collect()
        time.sleep(0.1)
        
        final_cycle = process.memory_info().rss / 1024 / 1024
        
        print(f"   Cycle {cycle + 1}: {before_cycle:.2f} → {after_cycle:.2f} → {final_cycle:.2f} MB")
        
        # Check for leaks
        leak = final_cycle - before_cycle
        if leak > 0.5:  # More than 0.5MB leak
            print(f"   ⚠️  Potential leak: {leak:.2f} MB")
        else:
            print(f"   ✅ OK: {leak:.2f} MB")

def test_queue_simulation() -> None:
    """Simulate queue behavior without full app."""
    print(f"\n🔍 Queue Simulation Test")
    print("=" * 25)
    
    import queue
    
    process = psutil.Process()
    
    # Simulate queues
    result_queue = queue.Queue()
    logging_queue = queue.Queue()
    
    print(f"🧪 Testing queue operations:")
    
    for cycle in range(3):
        before_cycle = process.memory_info().rss / 1024 / 1024
        
        # Add items to queues
        for i in range(100):
            result_queue.put({
                'file_path': f"test_file_{i}.jpg",
                'worker_id': i % 4,
                'success': True
            })
            
            logging_queue.put({
                'level': 'DEBUG',
                'message': f'Worker {i % 4} processed test_file_{i}.jpg'
            })
        
        after_add = process.memory_info().rss / 1024 / 1024
        
        # Process queues
        results = []
        logs = []
        
        while not result_queue.empty():
            results.append(result_queue.get())
        
        while not logging_queue.empty():
            logs.append(logging_queue.get())
        
        after_process = process.memory_info().rss / 1024 / 1024
        
        # Cleanup
        del results, logs
        gc.collect()
        time.sleep(0.1)
        
        final_cycle = process.memory_info().rss / 1024 / 1024
        
        print(f"   Cycle {cycle + 1}: {before_cycle:.2f} → {after_add:.2f} → {after_process:.2f} → {final_cycle:.2f} MB")
        
        # Check for leaks
        leak = final_cycle - before_cycle
        if leak > 0.5:  # More than 0.5MB leak
            print(f"   ⚠️  Potential leak: {leak:.2f} MB")
        else:
            print(f"   ✅ OK: {leak:.2f} MB")

def main() -> None:
    """Run working memory leak tests."""
    print("🧪 Fill Database V2 - Working Memory Testing")
    print("=" * 50)
    
    try:
        test_memory_basics()
        test_worker_simulation()
        test_queue_simulation()
        
        print(f"\n✅ Working memory testing completed successfully")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
