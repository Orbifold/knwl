import sys
import pytest


def main():
    sys.exit(pytest.main(["-m", "not llm"]))


if __name__ == "__main__":
    main()
