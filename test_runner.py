#!/usr/bin/env python3
"""
Test runner helper script for the knwl project.
Provides easy commands to run different categories of tests.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the output."""
    print(f"\n🚀 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("""
Usage: python test_runner.py <command>

Commands:
  unit      - Run only unit tests (no LLM dependencies)
  llm       - Run only LLM-dependent tests
  all       - Run all tests
  fast      - Run unit tests with minimal output
  coverage  - Run unit tests with coverage report
  help      - Show this help message
        """)
        return

    command = sys.argv[1].lower()
    
    # Ensure we're in the right directory
    if not Path("tests").exists():
        print("❌ No tests directory found. Make sure you're in the project root.")
        return

    # Base pytest command
    base_cmd = ["uv", "run", "pytest"]
    
    if command == "unit":
        cmd = base_cmd + ["-m", "not llm", "-v"]
        run_command(cmd, "Running unit tests (excluding LLM-dependent tests)")
        
    elif command == "llm":
        cmd = base_cmd + ["-m", "llm", "-v", "--tb=short"]
        print("⚠️  LLM tests require Ollama to be running locally!")
        print("Make sure you have Ollama installed and a model available.")
        run_command(cmd, "Running LLM-dependent tests")
        
    elif command == "all":
        print("Running all tests (unit tests first, then LLM tests)")
        success1 = run_command(base_cmd + ["-m", "not llm", "-v"], "Unit tests")
        success2 = run_command(base_cmd + ["-m", "llm", "-v", "--tb=short"], "LLM tests")
        if success1 and success2:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
    elif command == "fast":
        cmd = base_cmd + ["-m", "not llm", "-q", "--tb=line"]
        run_command(cmd, "Running fast unit tests")
        
    elif command == "coverage":
        cmd = base_cmd + ["-m", "not llm", "--cov=knwl", "--cov-report=html", "--cov-report=term"]
        run_command(cmd, "Running unit tests with coverage")
        print("📊 Coverage report generated in htmlcov/index.html")
        
    elif command == "help":
        main()  # Show help
        
    else:
        print(f"❌ Unknown command: {command}")
        main()  # Show help


if __name__ == "__main__":
    main()