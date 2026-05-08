import os
import logging
import logging.config
from datetime import date
from django.conf import settings

def get_logger(name: str = None) -> logging.Logger:
    '''
    Returns a logger for the given module.
    - Logs to console and file.
    - Rotates daily.
    - Keeps last 5 logs.
    '''
    dynamic_log_path = getattr(settings, "DYNAMIC_LOG_PATH", os.path.join(settings.BASE_DIR, "Logs"))
    log_directory = os.path.join(dynamic_log_path, "server_logs")
    os.makedirs(log_directory, exist_ok=True)
    
    http_log_file = os.path.join(log_directory, f"{date.today()}.log")
    
    http_schema = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "http": {
                "format": "%(asctime)s [%(levelname)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "http_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "http",
                "level": "INFO",
                "filename": http_log_file,
                "encoding": "utf-8",
                "when": "midnight",
                "backupCount": 5,
            },
        },
        "loggers": {
            "http_requests": {
                "handlers": ["http_file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(http_schema)
    return logging.getLogger("http_requests")