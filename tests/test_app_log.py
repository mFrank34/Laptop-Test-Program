import logging
import os
import tempfile
import unittest

from app_log import configure_logging


class AppLogTests(unittest.TestCase):
    def test_writes_entries_to_configured_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "program.log")
            logger, configured_path = configure_logging(path)
            try:
                logger.info("unit-test diagnostic entry")
                for handler in logger.handlers:
                    handler.flush()

                with open(configured_path, encoding="utf-8") as log_file:
                    contents = log_file.read()
                self.assertIn("INFO unit-test diagnostic entry", contents)
            finally:
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()

if __name__ == "__main__":
    unittest.main()