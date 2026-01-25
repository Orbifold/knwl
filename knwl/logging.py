import logging
from logging.handlers import RotatingFileHandler
import os

from knwl.framework_base import FrameworkBase
from knwl.utils import get_full_path


class Log(FrameworkBase):
    """
    A logging utility class that provides flexible logging capabilities with both file and console output.

    This class extends FrameworkBase to provide a configurable logging system that supports:
    - Rotating file logs with configurable size and backup count
    - Console logging output
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Exception logging with traceback
    - Callable interface for quick logging

    Args:
        *args: Variable length argument list passed to parent class
        **kwargs: Arbitrary keyword arguments, including:
            - override: Configuration override dictionary
            - Configuration parameters for logging.enabled, logging.level, and logging.path

    Attributes:
        enabled (bool): Whether logging is enabled (default: True)
        logging_level (str): The logging level as string (default: "INFO")
        path (str): Path to the log file (default: "$/user/default/knwl.log")
        logger (logging.Logger): The underlying Python logger instance

    Examples:
        >>> log = Log()
        >>> log.info("Application started")
        >>> log("Quick log message")
        >>> try:
        ...     raise ValueError("Error occurred")
        ... except Exception as e:
        ...     log(e)
        >>> log.shutdown()

    Note:
        - File logs are rotated at 10MB with 5 backup files retained
        - Handlers are only added once to prevent duplicates
        - If logging is disabled, messages are printed to stdout instead
        - This class does not use the DI `defaults` mechanism for configuration since this would create a circular dependency.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self._enabled = self.get_param(
            ["logging", "enabled"], args, kwargs, default=True, override=config
        )
        self.logging_level = self.get_param(
            ["logging", "level"], args, kwargs, default="INFO", override=config
        )
        self.path = self.get_param(
            ["logging", "path"],
            args,
            kwargs,
            default="$/user/default/knwl.log",
            override=config,
        )
        self.path = get_full_path(self.path)

        # Initialize logger
        self.logger = None
        if self._enabled:
            self.logger = logging.getLogger("knwl")
            # Prevent adding duplicate handlers
            if not self.logger.handlers:
                self.setup_logging()

    @property
    def enabled(self) -> bool:
        """
        Get the current logging enabled state.
        
        Returns:
            bool: True if logging is enabled, False otherwise
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """
        Enable or disable logging at runtime.
        
        When disabled, log messages will be printed to stdout instead of being logged to file.
        When re-enabled, the logger will be reinitialized if needed.
        
        Args:
            value (bool): True to enable logging, False to disable
        """
        self._enabled = value
        if value and not self.logger:
            # Re-initialize logger if it was previously disabled
            self.logger = logging.getLogger("knwl")
            if not self.logger.handlers:
                self.setup_logging()

    def __call__(self, *args, **kwargs):
        if args:
            arg0 = args[0]
            if isinstance(arg0, Exception):
                self.exception(arg0)
            else:
                self.info(str(arg0))
        else:
            raise ValueError(
                "You can only call the log directly with an exception or message."
            )

    def setup_logging(self):
        """Set up both file and console logging"""
        level = self.get_logging_level()

        # Set logger level
        self.logger.setLevel(level)

        # Set up file handler
        self.setup_file_logging(level)

        # Set up console handler
        self.setup_console_logging(level)

    def get_logging_level(self):
        """Convert string level to logging constant"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        if self.logging_level not in level_map:
            raise ValueError(f"Invalid LOGGING_LEVEL: {self.logging_level}")

        return level_map[self.logging_level]

    def setup_file_logging(self, level) -> None:
        """Set up rotating file handler"""
        try:
            file_handler = RotatingFileHandler(
                self.path,
                maxBytes=10 * 1024 * 1024,  # 10MB per file
                backupCount=5,  # Keep 5 backup files
                delay=True,  # Only create log file when needed
            )

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)

            self.logger.addHandler(file_handler)

        except Exception as e:
            print(f"Failed to set up file logging: {e}")

    def setup_console_logging(self, level) -> None:
        """Set up console handler"""
        try:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)

            self.logger.addHandler(console_handler)

        except Exception as e:
            print(f"Failed to set up console logging: {e}")

    def info(self, message: str) -> None:
        if self._enabled and self.logger:
            self.logger.info(message)
        # else:
        #     print(f"INFO: {message}")

    def error(self, message: str) -> None:
        if self._enabled and self.logger:
            self.logger.error(message)
        else:
            print(f"ERROR: {message}")

    def warning(self, message: str) -> None:
        if self._enabled and self.logger:
            self.logger.warning(message)
        else:
            print(f"WARNING: {message}")

    def warn(self, message: str) -> None:
        if self._enabled and self.logger:
            self.logger.warning(message)
        else:
            print(f"WARNING: {message}")

    def debug(self, message: str) -> None:
        if self._enabled and self.logger:
            self.logger.debug(message)
        else:
            print(f"DEBUG: {message}")

    def exception(self, e: Exception) -> None:
        """Logs an exception with traceback"""
        if self._enabled and self.logger:
            self.logger.exception(e)
        else:
            import traceback

            print(f"EXCEPTION: {e}")
            traceback.print_exc()

    def shutdown(self) -> None:
        """Shuts down the logging system"""
        if self.logger:
            for handler in self.logger.handlers[
                :
            ]:  # Copy list to avoid modification during iteration
                handler.close()
                self.logger.removeHandler(handler)
            print("Logging system shut down successfully.")

    def list_items(self, severity=None, amount: int = 10) -> list[str]:
        """
        Returns a list of log entries from the log file.

        Args:
            severity: Optional severity level to filter by (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            amount: Maximum number of log entries to return (default: 10)

        Returns:
            List of log entry strings, newest first
        """
        try:
            if not self.path or not os.path.exists(self.path):
                return []

            with open(self.path, "r") as f:
                lines = f.readlines()

            # Filter by severity if provided
            if severity:
                severity_upper = severity.upper()
                if severity_upper not in [
                    "DEBUG",
                    "INFO",
                    "WARNING",
                    "ERROR",
                    "CRITICAL",
                ]:
                    raise ValueError(f"Invalid severity level: {severity}")
                lines = [line for line in lines if severity_upper in line]

            # Return last 'amount' items, reversed to show newest first
            return [line.strip() for line in lines[-amount:]][::-1]

        except Exception as e:
            self.error(f"Failed to read log items: {e}")
            return []

    def clear_log(self) -> None:
        """
        Clears the log file by truncating its contents.
        """
        try:
            if not self.path or not os.path.exists(self.path):
                return

            with open(self.path, "w") as f:
                f.truncate(0)

            self.info("Log file cleared.")

        except Exception as e:
            self.error(f"Failed to clear log file: {e}")

log = Log()
