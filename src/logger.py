import logging
import sys

# Custom Formatter to include function name in log messages
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # get name of current running function
        record.function_name = record.funcName
        return super().format(record)

# Set up the custom formatter for the logger
formatter = CustomFormatter('[%(asctime)-s] [%(levelname)-5s] [%(filename)s:%(lineno)d]  %(message)-s', datefmt="%H:%M:%S")

# Function to get a logger instance
def get_logger(name):
    logger = logging.getLogger(name)
    # Check if handlers exist to avoid duplicate logs if imported multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
