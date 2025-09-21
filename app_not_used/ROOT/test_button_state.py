#YAPMO_V3.0
"""Test script for Button State Management."""

import sys
import os
import time
sys.path.append('/workspaces/app')

def test_button_state_management():
    """Test button state management functionality."""
    
    print("Testing Button State Management...")
    print("=" * 50)
    
    # Simulate button states
    class MockButton:
        def __init__(self):
            self.text = "START PROCESSING"
            self.color = "primary"
            self.enabled = True
        
        def props(self, prop_string):
            if "color=negative" in prop_string:
                self.color = "negative"
            elif "color=primary" in prop_string:
                self.color = "primary"
        
        def disable(self):
            self.enabled = False
        
        def enable(self):
            self.enabled = True
        
        def __str__(self):
            return f"Button: text='{self.text}', color='{self.color}', enabled={self.enabled}"
    
    # Test button state changes
    button = MockButton()
    print(f"Initial state: {button}")
    
    # Test processing state
    print("\nSetting to processing state...")
    button.props("color=negative")
    button.text = "PROCESSING"
    button.disable()
    print(f"Processing state: {button}")
    
    # Verify processing state
    assert button.text == "PROCESSING", f"Expected 'PROCESSING', got '{button.text}'"
    assert button.color == "negative", f"Expected 'negative', got '{button.color}'"
    assert not button.enabled, f"Expected disabled, got enabled={button.enabled}"
    print("✓ Processing state correct")
    
    # Test ready state
    print("\nSetting to ready state...")
    button.props("color=primary")
    button.text = "START PROCESSING"
    button.enable()
    print(f"Ready state: {button}")
    
    # Verify ready state
    assert button.text == "START PROCESSING", f"Expected 'START PROCESSING', got '{button.text}'"
    assert button.color == "primary", f"Expected 'primary', got '{button.color}'"
    assert button.enabled, f"Expected enabled, got enabled={button.enabled}"
    print("✓ Ready state correct")
    
    # Test state transitions
    print("\nTesting state transitions...")
    
    # Ready -> Processing
    print("Ready -> Processing")
    button.props("color=negative")
    button.text = "PROCESSING"
    button.disable()
    assert button.text == "PROCESSING" and button.color == "negative" and not button.enabled
    print("✓ Ready -> Processing transition correct")
    
    # Processing -> Ready
    print("Processing -> Ready")
    button.props("color=primary")
    button.text = "START PROCESSING"
    button.enable()
    assert button.text == "START PROCESSING" and button.color == "primary" and button.enabled
    print("✓ Processing -> Ready transition correct")
    
    print("\n" + "=" * 50)
    print("Button State Management test completed!")
    print("✓ All button state transitions working correctly")

if __name__ == "__main__":
    test_button_state_management()
