import logging
from logging.handlers import RotatingFileHandler
from knwl.framework_base import FrameworkBase

from knwl.utils import get_full_path

# logger = logging.getLogger("knwl")


# # disable logging if not enabled in the settings
# if not get_config("logging", "enabled", default=True):
#     logger.setLevel(logging.CRITICAL)
#     return logger
# logging.basicConfig(
#     force=True,
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)s %(message)s",
#     handlers=[
#         logging.FileHandler(get_config("logging", "path", default="knwl.log")),
#         logging.StreamHandler()
#     ],
# )


class Log(FrameworkBase):
    logger = None

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
        if self.enabled:
            self.logger = logging.getLogger("knwl")

            self.set_level()
            self.setup_file_logging()

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

    def set_level(self):
        if self.logging_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid LOGGING_LEVEL: {self.logging_level}")
        else:
            print(f"Setting logging level to {self.logging_level}")
        if self.logging_level == "DEBUG":
            self.logging_level = logging.DEBUG
        elif self.logging_level == "INFO":
            self.logging_level = logging.INFO
        elif self.logging_level == "WARNING":
            self.logging_level = logging.WARNING
        elif self.logging_level == "ERROR":
            self.logging_level = logging.ERROR
        elif self.logging_level == "CRITICAL":
            self.logging_level = logging.CRITICAL

    def setup_file_logging(self) -> None:
        try:

            file_handler = RotatingFileHandler(
                self.path,
                maxBytes=10 * 1024 * 1024,  # 10MB per file
                backupCount=5,  # Keep 5 backup files
                delay=True,  # Only create log file when needed
            )

            # Set formatting for file logs
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(self.logging_level)

            self.logger.addHandler(file_handler)

        except Exception as e:
            print(f"Failed to set up file logging: {e}")

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
        """
        Logs an exception with traceback.
        """
        if self.logger:
            self.logger.exception(e)
        else:
            print(f"EXCEPTION: {e}")

    def shutdown(self) -> None:
        """
        Shuts down the logging system, flushing all logs and closing handlers.
        """
        if self.logger:
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)
            logging.shutdown()
            print("Logging system shut down successfully.")
        else:
            print("No logger to shut down.")


log = Log()
