import logging
import os

LOG_FILE = os.path.join(os.getcwd(), "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Saves to file
        logging.StreamHandler(),  # Also prints to console
    ],
)

logger = logging.getLogger(__name__)
