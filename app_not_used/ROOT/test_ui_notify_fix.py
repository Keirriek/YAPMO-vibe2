#YAPMO_V3.0
"""Test script to verify ui.notify fix."""

import sys
import os
sys.path.append('/workspaces/app')

def test_ui_notify_fix():
    """Test that ui.notify calls are removed from background threads."""
    
    print("Testing UI Notify Fix...")
    print("=" * 50)
    
    # Read the fill_db_new.py file
    with open('/workspaces/app/pages/fill_db_new.py', 'r') as f:
        content = f.read()
    
    # Check for ui.notify calls in background thread functions
    background_thread_functions = [
        '_run_file_processing',
        '_file_processing_progress_callback',
        '_handle_processing_completion'
    ]
    
    print("Checking background thread functions...")
    print("-" * 30)
    
    for func_name in background_thread_functions:
        print(f"\nChecking {func_name}():")
        
        # Find function definition
        func_start = content.find(f'def {func_name}(')
        if func_start == -1:
            print(f"  ✗ Function {func_name} not found")
            continue
            
        # Find function end (next def or class)
        func_end = content.find('\n    def ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\nclass ', func_start + 1)
        if func_end == -1:
            func_end = len(content)
            
        func_content = content[func_start:func_end]
        
        # Check for ui.notify calls
        ui_notify_calls = func_content.count('ui.notify(')
        if ui_notify_calls == 0:
            print(f"  ✓ No ui.notify calls found")
        else:
            print(f"  ✗ Found {ui_notify_calls} ui.notify calls")
            # Show the lines with ui.notify
            lines = func_content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'ui.notify(' in line:
                    print(f"    Line {i}: {line.strip()}")
    
    # Check main thread functions (these should still have ui.notify)
    main_thread_functions = [
        '_start_file_processing',
        '_select_directory',
        '_browse_directory',
        '_validate_directory'
    ]
    
    print(f"\nChecking main thread functions...")
    print("-" * 30)
    
    for func_name in main_thread_functions:
        print(f"\nChecking {func_name}():")
        
        # Find function definition
        func_start = content.find(f'def {func_name}(')
        if func_start == -1:
            print(f"  - Function {func_name} not found")
            continue
            
        # Find function end
        func_end = content.find('\n    def ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\nclass ', func_start + 1)
        if func_end == -1:
            func_end = len(content)
            
        func_content = content[func_start:func_end]
        
        # Check for ui.notify calls
        ui_notify_calls = func_content.count('ui.notify(')
        if ui_notify_calls > 0:
            print(f"  ✓ Found {ui_notify_calls} ui.notify calls (OK for main thread)")
        else:
            print(f"  - No ui.notify calls found")
    
    print("\n" + "=" * 50)
    print("UI Notify Fix test completed!")
    print("✓ Background threads should not have ui.notify calls")
    print("✓ Main thread functions can still have ui.notify calls")

if __name__ == "__main__":
    test_ui_notify_fix()
