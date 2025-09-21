#YAPMO_V3.0
"""Debug UI update issues."""

import sys
import os
sys.path.append('/workspaces/app')

def test_ui_update_debug():
    """Debug UI update issues."""
    
    print("Debugging UI Update Issues...")
    print("=" * 50)
    
    # Read the fill_db_new.py file
    with open('/workspaces/app/pages/fill_db_new.py', 'r') as f:
        content = f.read()
    
    # Check if _update_file_processing_display exists
    if '_update_file_processing_display' in content:
        print("✓ _update_file_processing_display method exists")
    else:
        print("✗ _update_file_processing_display method missing")
    
    # Check if UI update manager is properly set up
    if 'register_callback' in content and 'processing_progress' in content:
        print("✓ UI update manager callback registration found")
    else:
        print("✗ UI update manager callback registration missing")
    
    # Check if _file_processing_progress_callback calls _update_file_processing_display
    if '_file_processing_progress_callback' in content:
        # Find the method
        start = content.find('def _file_processing_progress_callback')
        if start != -1:
            end = content.find('\n    def ', start + 1)
            if end == -1:
                end = len(content)
            method_content = content[start:end]
            
            if '_update_file_processing_display' in method_content:
                print("✓ _file_processing_progress_callback calls _update_file_processing_display")
            else:
                print("✗ _file_processing_progress_callback does not call _update_file_processing_display")
    
    # Check if _handle_processing_completion calls _set_button_ready
    if '_handle_processing_completion' in content:
        start = content.find('def _handle_processing_completion')
        if start != -1:
            end = content.find('\n    def ', start + 1)
            if end == -1:
                end = len(content)
            method_content = content[start:end]
            
            if '_set_button_ready' in method_content:
                print("✓ _handle_processing_completion calls _set_button_ready")
            else:
                print("✗ _handle_processing_completion does not call _set_button_ready")
    
    # Check if _run_file_processing calls _handle_processing_completion
    if '_run_file_processing' in content:
        start = content.find('def _run_file_processing')
        if start != -1:
            end = content.find('\n    def ', start + 1)
            if end == -1:
                end = len(content)
            method_content = content[start:end]
            
            if '_handle_processing_completion' in method_content:
                print("✓ _run_file_processing calls _handle_processing_completion")
            else:
                print("✗ _run_file_processing does not call _handle_processing_completion")
    
    print("\n" + "=" * 50)
    print("UI Update Debug completed!")

if __name__ == "__main__":
    test_ui_update_debug()
