"""File logging for application diagnostics."""

import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler


LOGGER = logging.getLogger("laptop_test")
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False


def configure_logging(path=None):
    """Configure a small rotating log and return (logger, log_path)."""
    path = os.path.abspath(
        path or os.environ.get(
            "LAPTOP_TEST_LOG", os.path.join(tempfile.gettempdir(), "laptop-test.log")
        )
    )
    if not any(
        isinstance(handler, RotatingFileHandler)
        and handler.baseFilename == path
        for handler in LOGGER.handlers
    ):
        for handler in LOGGER.handlers[:]:
            LOGGER.removeHandler(handler)
            handler.close()
        handler = RotatingFileHandler(
            path, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        LOGGER.addHandler(handler)
    return LOGGER, path