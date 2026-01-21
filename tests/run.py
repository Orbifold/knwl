import sys
import pytest


def main():
    sys.exit(pytest.main(["-m", "not llm and not integration"]))


if __name__ == "__main__":
    main()
