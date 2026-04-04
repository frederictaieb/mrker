# utils/logger.py

import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(lineno)d - %(message)s"
        )

        # Console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Fichier
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger