import logging
import os
import tempfile
from pathlib import Path
from unittest import mock
import pytest
from knwl.logging import Log

class TestLog:
    """Test suite for Log class"""

    def setup_method(self):
        """Setup for each test - clear handlers"""
        logger = logging.getLogger("knwl")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    def teardown_method(self):
        """Cleanup after each test"""
        logger = logging.getLogger("knwl")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    def test_log_initialization_default(self):
        """Test Log initialization with default settings"""
        log = Log()
        assert log.enabled is True
        assert log.logging_level == "INFO"
        assert log.logger is not None
        assert log.logger.name == "knwl"
        log.shutdown()

    def test_log_initialization_with_override(self):
        """Test Log initialization with config override"""
        override = {
            "logging": {
                "enabled": True,
                "level": "DEBUG",
                "path": "$/user/test/test.log"
            }
        }
        log = Log(override=override)
        assert log.enabled is True
        assert log.logging_level == "DEBUG"
        assert "test.log" in log.path
        log.shutdown()

    def test_log_disabled(self):
        """Test Log when logging is disabled"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        assert log.enabled is False
        assert log.logger is None
        log.shutdown()

    def test_log_levels(self):
        """Test different logging levels"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            override = {"logging": {"level": level}}
            log = Log(override=override)
            assert log.logging_level == level
            log.shutdown()

    def test_invalid_log_level(self):
        """Test that invalid log level raises ValueError"""
        override = {"logging": {"level": "INVALID"}}
        with pytest.raises(ValueError, match="Invalid LOGGING_LEVEL"):
            Log(override=override)

    def test_info_logging(self, capsys):
        """Test info level logging"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        log.info("Test info message")
        captured = capsys.readouterr()
        assert "INFO: Test info message" in captured.out
        log.shutdown()

    def test_error_logging(self, capsys):
        """Test error level logging"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        log.error("Test error message")
        captured = capsys.readouterr()
        assert "ERROR: Test error message" in captured.out
        log.shutdown()

    def test_warning_logging(self, capsys):
        """Test warning level logging"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        log.warning("Test warning message")
        captured = capsys.readouterr()
        assert "WARNING: Test warning message" in captured.out
        log.shutdown()

    def test_warn_logging(self, capsys):
        """Test warn (alias for warning) level logging"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        log.warn("Test warn message")
        captured = capsys.readouterr()
        assert "WARNING: Test warn message" in captured.out
        log.shutdown()

    def test_debug_logging(self, capsys):
        """Test debug level logging"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        log.debug("Test debug message")
        captured = capsys.readouterr()
        assert "DEBUG: Test debug message" in captured.out
        log.shutdown()

    def test_exception_logging(self, capsys):
        """Test exception logging"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        try:
            raise ValueError("Test exception")
        except Exception as e:
            log.exception(e)
        captured = capsys.readouterr()
        assert "EXCEPTION: Test exception" in captured.out
        log.shutdown()

    def test_callable_with_message(self, capsys):
        """Test calling Log instance with a message"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        log("Test callable message")
        captured = capsys.readouterr()
        assert "INFO: Test callable message" in captured.out
        log.shutdown()

    def test_callable_with_exception(self, capsys):
        """Test calling Log instance with an exception"""
        override = {"logging": {"enabled": False}}
        log = Log(override=override)
        try:
            raise RuntimeError("Test runtime error")
        except Exception as e:
            log(e)
        captured = capsys.readouterr()
        assert "EXCEPTION: Test runtime error" in captured.out
        log.shutdown()

    def test_callable_without_args(self):
        """Test calling Log instance without arguments raises ValueError"""
        log = Log()
        with pytest.raises(ValueError, match="You can only call the log directly"):
            log()
        log.shutdown()

    def test_file_logging_creation(self):
        """Test that file logging creates log file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            override = {"logging": {"path": str(log_path)}}
            log = Log(override=override)
            log.info("Test message")
            log.shutdown()
            assert log_path.exists()

    def test_no_duplicate_handlers(self):
        """Test that handlers are not duplicated"""
        log1 = Log()
        initial_handler_count = len(log1.logger.handlers)
        log1.shutdown()
        
        log2 = Log()
        assert len(log2.logger.handlers) == initial_handler_count
        log2.shutdown()

    def test_shutdown(self, capsys):
        """Test shutdown closes and removes handlers"""
        log = Log()
        log.shutdown()
        captured = capsys.readouterr()
        assert "Logging system shut down successfully" in captured.out
        assert len(log.logger.handlers) == 0

    def test_file_handler_rotation_config(self):
        """Test that file handler is configured with rotation settings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            override = {"logging": {"path": str(log_path)}}
            log = Log(override=override)
            
            # Find the rotating file handler
            file_handler = None
            for handler in log.logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    file_handler = handler
                    break
            
            assert file_handler is not None
            assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
            assert file_handler.backupCount == 5
            log.shutdown()

    def test_console_handler_exists(self):
        """Test that console handler is added"""
        log = Log()
        
        has_console_handler = any(
            isinstance(handler, logging.StreamHandler)
            for handler in log.logger.handlers
        )
        
        assert has_console_handler is True
        log.shutdown()

    @mock.patch('knwl.logging.RotatingFileHandler')
    def test_file_logging_failure_handling(self, mock_handler, capsys):
        """Test graceful handling of file logging setup failure"""
        mock_handler.side_effect = Exception("File creation failed")
        
        log = Log()
        captured = capsys.readouterr()
        assert "Failed to set up file logging" in captured.out
        log.shutdown()

    @mock.patch('logging.StreamHandler')
    def test_console_logging_failure_handling(self, mock_handler, capsys):
        """Test graceful handling of console logging setup failure"""
        mock_handler.side_effect = Exception("Console handler failed")
        
        log = Log()
        captured = capsys.readouterr()
        assert "Failed to set up console logging" in captured.out
        log.shutdown()