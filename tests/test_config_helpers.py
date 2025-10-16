"""
Test configuration utilities for KNWL unit tests.
Provides helper functions for setting up test environments and managing environment variables.
"""

import os
import pytest
from typing import Dict, Any, Optional
from unittest.mock import patch


class TestEnvManager:
    """Context manager for temporarily setting environment variables during tests."""
    
    def __init__(self, env_vars: Dict[str, str]):
        self.env_vars = env_vars
        self.original_vars = {}
        
    def __enter__(self):
        # Store original values
        for key in self.env_vars:
            self.original_vars[key] = os.environ.get(key)
            
        # Set new values
        for key, value in self.env_vars.items():
            os.environ[key] = value
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original values
        for key, original_value in self.original_vars.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def get_test_config() -> Dict[str, Any]:
    """Get configuration settings optimized for testing."""
    return {
        "api": {
            "development": True,
            "host": "localhost",
            "port": 9001,
        },
        "logging": {
            "enabled": False,  # Disable logging in tests by default
            "level": "ERROR",
        },
        "llm": {
            "openai": {
                "model": "gpt-3.5-turbo",  # Cheaper model for tests
                "temperature": 0.0,  # Deterministic outputs
                "max_tokens": 100,  # Limit tokens in tests
            }
        }
    }


def skip_if_no_api_key(api_key_env_var: str = "OPENAI_API_KEY"):
    """Decorator to skip tests if API key is not available."""
    return pytest.mark.skipif(
        not os.getenv(api_key_env_var),
        reason=f"{api_key_env_var} environment variable not set"
    )


def mock_env_vars(**kwargs):
    """Decorator to mock environment variables for a test."""
    def decorator(func):
        def wrapper(*args, **test_kwargs):
            with patch.dict(os.environ, kwargs):
                return func(*args, **test_kwargs)
        return wrapper
    return decorator


# Pytest fixtures
@pytest.fixture
def test_env():
    """Fixture that provides a clean test environment."""
    test_vars = {
        "KNWL_ENV": "test",
        "KNWL_LOG_LEVEL": "ERROR",
    }
    
    with TestEnvManager(test_vars):
        yield


@pytest.fixture  
def mock_openai_key():
    """Fixture that provides a mock OpenAI API key for testing."""
    test_vars = {
        "OPENAI_API_KEY": "sk-test-mock-api-key-for-testing-123456789"
    }
    
    with TestEnvManager(test_vars):
        yield