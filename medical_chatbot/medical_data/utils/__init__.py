import logging
from logging.handlers import RotatingFileHandler
from medical_data.utils.util import get_config

logger = logging.getLogger('PatternPredictor')
logger.setLevel(logging.INFO)
logger.propagate = False

# Define formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create console handler for output to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Create a file handler for output to file, with log rotation
log_path = get_config('paths', 'logs_path')
file_handler = RotatingFileHandler(
    log_path,
    maxBytes=1024 * 1024 * 5,  # 5 MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

