import logging
from logging.handlers import RotatingFileHandler
from knwl.framework_base import FrameworkBase
from knwl.utils import get_full_path

class Log(FrameworkBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = kwargs.get("override", None)
        self.enabled = self.get_param(
            ["logging", "enabled"], args, kwargs, default=True, override=config
        )
        self.logging_level = self.get_param(
            ["logging", "level"], args, kwargs, default="INFO", override=config
        )
        self.path = self.get_param(
            ["logging", "path"], args, kwargs, default="$root/knwl.log", override=config
        )
        self.path = get_full_path(self.path)
        
        # Initialize logger
        self.logger = None
        if self.enabled:
            self.logger = logging.getLogger("knwl")
            # Prevent adding duplicate handlers
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
            "CRITICAL": logging.CRITICAL
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
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            
            self.logger.addHandler(console_handler)

        except Exception as e:
            print(f"Failed to set up console logging: {e}")

    def info(self, message: str) -> None:
        if self.logger:
            self.logger.info(message)
        else:
            print(f"INFO: {message}")

    def error(self, message: str) -> None:
        if self.logger:
            self.logger.error(message)
        else:
            print(f"ERROR: {message}")

    def warning(self, message: str) -> None:
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"WARNING: {message}")

    def debug(self, message: str) -> None:
        if self.logger:
            self.logger.debug(message)
        else:
            print(f"DEBUG: {message}")

    def exception(self, e: Exception) -> None:
        """Logs an exception with traceback"""
        if self.logger:
            self.logger.exception(e)
        else:
            import traceback
            print(f"EXCEPTION: {e}")
            traceback.print_exc()

    def shutdown(self) -> None:
        """Shuts down the logging system"""
        if self.logger:
            for handler in self.logger.handlers[:]:  # Copy list to avoid modification during iteration
                handler.close()
                self.logger.removeHandler(handler)
            print("Logging system shut down successfully.")

log = Log()