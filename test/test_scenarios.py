#!/usr/bin/env python3
"""
Test Scenarios voor Fill Database V2 Memory Testing

Definieert test scenario's voor memory leak testing
"""

from pathlib import Path
from typing import List, Dict, Any

class TestScenario:
    """Test scenario voor memory testing."""
    
    def __init__(self, name: str, description: str, steps: List[str]):
        """Initialize test scenario."""
        self.name = name
        self.description = description
        self.steps = steps
    
    def __str__(self) -> str:
        """String representation of test scenario."""
        return f"{self.name}: {self.description}"

# Test scenario's
TEST_SCENARIOS = [
    TestScenario(
        name="Large Directory Scan",
        description="Scan een grote directory met veel bestanden",
        steps=[
            "1. Start de app (cd /workspaces/app && poetry run python main.py)",
            "2. Start memory monitor (cd /workspaces && poetry run python test/memory_monitor.py)",
            "3. Selecteer een grote directory (10.000+ bestanden)",
            "4. Klik 'START Scanning'",
            "5. Wacht tot scan compleet is",
            "6. Stop memory monitor (Ctrl+C)",
            "7. Check memory report voor leaks"
        ]
    ),
    
    TestScenario(
        name="Large File Processing",
        description="Process een grote set bestanden",
        steps=[
            "1. Start de app (cd /workspaces/app && poetry run python main.py)",
            "2. Start memory monitor (cd /workspaces && poetry run python test/memory_monitor.py)",
            "3. Scan een directory eerst",
            "4. Klik 'START PROCESSING'",
            "5. Wacht tot processing compleet is",
            "6. Stop memory monitor (Ctrl+C)",
            "7. Check memory report voor leaks"
        ]
    ),
    
    TestScenario(
        name="Multiple Scan Cycles",
        description="Herhaalde scan cycles om memory leaks te detecteren",
        steps=[
            "1. Start de app (cd /workspaces/app && poetry run python main.py)",
            "2. Start memory monitor (cd /workspaces && poetry run python test/memory_monitor.py)",
            "3. Scan directory 1",
            "4. Wacht tot IDLE state",
            "5. Scan directory 2",
            "6. Wacht tot IDLE state",
            "7. Scan directory 3",
            "8. Wacht tot IDLE state",
            "9. Stop memory monitor (Ctrl+C)",
            "10. Check memory report voor leaks"
        ]
    ),
    
    TestScenario(
        name="Multiple Processing Cycles",
        description="Herhaalde processing cycles om memory leaks te detecteren",
        steps=[
            "1. Start de app (cd /workspaces/app && poetry run python main.py)",
            "2. Start memory monitor (cd /workspaces && poetry run python test/memory_monitor.py)",
            "3. Scan directory",
            "4. Process files",
            "5. Wacht tot IDLE state",
            "6. Scan directory opnieuw",
            "7. Process files opnieuw",
            "8. Wacht tot IDLE state",
            "9. Herhaal 2-3 keer",
            "10. Stop memory monitor (Ctrl+C)",
            "11. Check memory report voor leaks"
        ]
    ),
    
    TestScenario(
        name="Abort Testing",
        description="Test abort functionaliteit voor memory leaks",
        steps=[
            "1. Start de app (cd /workspaces/app && poetry run python main.py)",
            "2. Start memory monitor (cd /workspaces && poetry run python test/memory_monitor.py)",
            "3. Start scanning",
            "4. Klik ABORT tijdens scanning",
            "5. Wacht tot IDLE state",
            "6. Start processing",
            "7. Klik ABORT tijdens processing",
            "8. Wacht tot IDLE state",
            "9. Herhaal 2-3 keer",
            "10. Stop memory monitor (Ctrl+C)",
            "11. Check memory report voor leaks"
        ]
    ),
    
    TestScenario(
        name="Mixed Operations",
        description="Mix van verschillende operaties om complexe leaks te detecteren",
        steps=[
            "1. Start de app (cd /workspaces/app && poetry run python main.py)",
            "2. Start memory monitor (cd /workspaces && poetry run python test/memory_monitor.py)",
            "3. Scan directory A",
            "4. Process files",
            "5. Scan directory B",
            "6. Abort processing",
            "7. Scan directory C",
            "8. Process files",
            "9. Scan directory A opnieuw",
            "10. Process files opnieuw",
            "11. Stop memory monitor (Ctrl+C)",
            "12. Check memory report voor leaks"
        ]
    )
]

def print_scenarios() -> None:
    """Print all available test scenarios."""
    print("🧪 Fill Database V2 - Test Scenarios")
    print("=" * 40)
    print()
    
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"{i}. {scenario.name}")
        print(f"   {scenario.description}")
        print()
        print("   Steps:")
        for step in scenario.steps:
            print(f"   {step}")
        print()
        print("-" * 40)
        print()

def get_scenario(scenario_number: int) -> TestScenario:
    """Get test scenario by number."""
    if 1 <= scenario_number <= len(TEST_SCENARIOS):
        return TEST_SCENARIOS[scenario_number - 1]
    else:
        raise ValueError(f"Invalid scenario number: {scenario_number}")

def create_test_directories() -> None:
    """Create test directories with dummy files."""
    print("📁 Creating test directories...")
    
    # Create test directories
    test_dirs = [
        "/workspaces/test/large_scan_1",
        "/workspaces/test/large_scan_2", 
        "/workspaces/test/large_scan_3",
        "/workspaces/test/processing_test"
    ]
    
    for test_dir in test_dirs:
        dir_path = Path(test_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create dummy files
        for i in range(100):  # 100 files per directory
            (dir_path / f"test_image_{i:03d}.jpg").write_text(f"Dummy image content {i}")
            (dir_path / f"test_video_{i:03d}.mp4").write_text(f"Dummy video content {i}")
            (dir_path / f"test_sidecar_{i:03d}.xmp").write_text(f"Dummy sidecar content {i}")
        
        print(f"   ✅ Created {test_dir} with 300 files")
    
    print("✅ Test directories created successfully")

def main() -> None:
    """Main function."""
    print("🧪 Fill Database V2 - Test Scenario Manager")
    print("=" * 50)
    print()
    
    print("Available test scenarios:")
    print_scenarios()
    
    print("To run a scenario:")
    print("1. Choose a scenario number (1-6)")
    print("2. Follow the steps in the scenario")
    print("3. Use memory_monitor.py to monitor memory usage")
    print()
    
    print("Quick start:")
    print("1. cd /workspaces && poetry run python test/memory_monitor.py  # Start monitoring")
    print("2. cd /workspaces/app && poetry run python main.py             # Start app")
    print("3. Follow scenario steps")
    print("4. Ctrl+C to stop monitoring")
    print("5. Check memory report")

if __name__ == "__main__":
    main()
