#!/usr/bin/env python3
"""Script to add TEST_AI_OFF markers to active test functions."""

import re

def fix_test_ai_markers():
    """Add TEST_AI_OFF markers to active test functions."""
    
    print("Adding TEST_AI_OFF markers to active test functions...")
    
    # Read the fill_db_new.py file
    with open('/workspaces/app/pages/fill_db_new.py', 'r') as f:
        content = f.read()
    
    # Pattern to match TEST_AI logging that doesn't already have a marker
    # This matches logging_service.log("TEST_AI", ...) that are not already marked with #TEST_AI
    pattern = r'(logging_service\.log\("TEST_AI", [^)]+\))(?!#TEST_AI)'
    
    # Find all matches
    matches = re.findall(pattern, content)
    
    # Replace with TEST_AI_OFF markers
    def replace_func(match):
        return match.group(1) + '#TEST_AI_OFF'
    
    new_content = re.sub(pattern, replace_func, content)
    
    # Write the modified content back
    with open('/workspaces/app/pages/fill_db_new.py', 'w') as f:
        f.write(new_content)
    
    print(f"✓ Added TEST_AI_OFF markers to {len(matches)} TEST_AI logging statements")
    print("✓ Active test functions now have proper markers")

if __name__ == "__main__":
    fix_test_ai_markers()
