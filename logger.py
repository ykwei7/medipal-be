import logging
import logging.handlers
from logging.handlers import RotatingFileHandler

LOG_FILENAME = "log/medipal.log"

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(LOG_FILENAME, maxBytes=1024 * 1024 * 50,
                                  backupCount=20)
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)