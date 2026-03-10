"""
Logging configuration for the application.
Sets up file and console logging handlers.
"""
import logging
import logging.handlers
from pathlib import Path
import sys

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def setup_logging():
    """Configure logging for the application."""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - main app log
    app_log_file = LOGS_DIR / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # File handler - error log
    error_log_file = LOGS_DIR / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # File handler - celery/worker log
    worker_log_file = LOGS_DIR / "worker.log"
    worker_handler = logging.handlers.RotatingFileHandler(
        worker_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    worker_handler.setLevel(logging.INFO)
    worker_handler.setFormatter(formatter)
    
    # Add worker handler to celery and worker loggers
    logging.getLogger('celery').addHandler(worker_handler)
    logging.getLogger('app.workers').addHandler(worker_handler)
    
    # Reduce noise from some libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    logging.info(f"Logging configured. Logs directory: {LOGS_DIR}")
    logging.info(f"App log: {app_log_file}")
    logging.info(f"Error log: {error_log_file}")
    logging.info(f"Worker log: {worker_log_file}")

# Call setup when module is imported
setup_logging()
