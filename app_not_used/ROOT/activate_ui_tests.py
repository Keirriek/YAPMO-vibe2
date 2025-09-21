#!/usr/bin/env python3
"""Script to activate UI update tests by removing comments."""

import re

def activate_ui_tests():
    """Activate UI update tests by removing #TEST_AI_OFF comments."""
    
    print("Activating UI Update Tests...")
    print("=" * 50)
    
    # Read the fill_db_new.py file
    with open('/workspaces/app/pages/fill_db_new.py', 'r') as f:
        content = f.read()
    
    # Count original lines
    original_lines = content.count('\n')
    
    # Remove #TEST_AI_OFF comments and uncomment test functions
    modifications = [
        # Remove #TEST_AI_OFF comments
        (r'#TEST_AI_OFF Start Block.*?\n', ''),
        (r'#TEST_AI_OFF End Block.*?\n', ''),
        (r'#TEST_AI_OFF.*?\n', ''),
        
        # Uncomment test function definitions
        (r'# def _test_ui_update_manager_state_awareness', 'def _test_ui_update_manager_state_awareness'),
        (r'# def _test_file_processing_display_state_awareness', 'def _test_file_processing_display_state_awareness'),
        (r'# def _test_log_display_state_awareness', 'def _test_log_display_state_awareness'),
        (r'# def _test_progress_display_state_awareness', 'def _test_progress_display_state_awareness'),
        
        # Uncomment test function calls
        (r'# self\._test_ui_update_manager_state_awareness\(\)', 'self._test_ui_update_manager_state_awareness()'),
        (r'# self\._test_file_processing_display_state_awareness\(\)', 'self._test_file_processing_display_state_awareness()'),
        (r'# self\._test_log_display_state_awareness\(\)', 'self._test_log_display_state_awareness()'),
        (r'# self\._test_progress_display_state_awareness\(\)', 'self._test_progress_display_state_awareness()'),
        
        # Uncomment test function bodies (remove # from start of lines)
        (r'^    #     ', '        '),
        (r'^    #         ', '            '),
        (r'^    #             ', '                '),
        (r'^    #                 ', '                    '),
    ]
    
    modified_content = content
    changes_made = 0
    
    for pattern, replacement in modifications:
        new_content = re.sub(pattern, replacement, modified_content, flags=re.MULTILINE)
        if new_content != modified_content:
            changes_made += 1
            modified_content = new_content
    
    # Write the modified content back
    with open('/workspaces/app/pages/fill_db_new.py', 'w') as f:
        f.write(modified_content)
    
    # Count new lines
    new_lines = modified_content.count('\n')
    
    print(f"✓ Made {changes_made} modifications")
    print(f"✓ Original lines: {original_lines}")
    print(f"✓ New lines: {new_lines}")
    print(f"✓ Lines removed: {original_lines - new_lines}")
    
    print("\n" + "=" * 50)
    print("UI Update Tests Activated!")
    print("\nNext steps:")
    print("1. Run: python test_ui_update_debug.py")
    print("2. Run: poetry run python main.py")
    print("3. Check the log for TEST_AI messages")
    print("4. Test scan and processing operations")

if __name__ == "__main__":
    activate_ui_tests()
