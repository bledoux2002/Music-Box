import logging
import os
import sys
from pathlib import Path


LOG_DIRECTORY_NAME = 'logs'
LOG_FILE_NAME = 'music_box.log'


def get_log_file_path():
    """Return the application log path and create its directory."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).resolve().parent
    else:
        base_path = Path(__file__).resolve().parent

    log_directory = base_path / LOG_DIRECTORY_NAME
    log_directory.mkdir(parents=True, exist_ok=True)
    return log_directory / LOG_FILE_NAME


def configure_logging():
    """Configure and return the application logger."""
    logger = logging.getLogger('music_box')
    if logger.handlers:
        return logger

    log_file_path = get_log_file_path()
    handler = logging.FileHandler(log_file_path, encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info('Logging initialized at %s', os.fspath(log_file_path))
    return logger
