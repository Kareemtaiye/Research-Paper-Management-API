import logging
import os
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
# --- v1 ---

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
#     handlers=[
#         logging.FileHandler(LOG_FILE),  # Saves to file
#         logging.StreamHandler(),  # Also prints to console
#     ],
# )


LOG_FILE = os.path.join(os.getcwd(), "app.log")


def setup_logging():
    logger = logging.getLogger()

    # JSON handler for structured logs
    json_handler = logging.StreamHandler()
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    json_handler.setFormatter(json_formatter)

    # File handler — keeps your existing file logging
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(json_formatter)  # JSON in file too

    logger.addHandler(json_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    return logger


logger = setup_logging()
