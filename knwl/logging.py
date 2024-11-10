import logging
from knwl.settings import settings


logger = logging.getLogger("knwl")


def set_logger():
    """
    Sets up a logger with the specified log file.
    This function configures the logging module to log messages to a file.
    The log level is set to DEBUG, and the log format includes the timestamp,
    log level, and message.

    Returns:
        logging.Logger: The configured logger instance.
    """
    # disable logging if not enabled in the settings
    if not settings.logging_enabled:
        logger.setLevel(logging.CRITICAL)
        return logger
    logging.basicConfig(
        force=True,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ],
    )
    logger.info("Logger is set up")
    return logger
