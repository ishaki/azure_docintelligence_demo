"""Logging configuration for the Document Intelligence application."""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Configures application logging."""
    
    def __init__(self, log_dir: Optional[Path] = None) -> None:
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory for log files. Defaults to 'logs' directory in project root.
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_file = self.log_dir / "app.log"
        self.error_log_file = self.log_dir / "error.log"
    
    def setup_logging(self, level: int = logging.INFO) -> None:
        """
        Setup application-wide logging configuration.
        
        Args:
            level: Logging level (default: INFO)
        """
        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers = []
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs (daily rotation, keep 30 days)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(self.log_file),
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        file_handler.suffix = '%Y-%m-%d'
        root_logger.addHandler(file_handler)
        
        # Error file handler (ERROR and above, daily rotation, keep 90 days)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(self.error_log_file),
            when='midnight',
            interval=1,
            backupCount=90,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        error_handler.suffix = '%Y-%m-%d'
        root_logger.addHandler(error_handler)
        
        # Set levels for third-party libraries
        logging.getLogger('uvicorn').setLevel(logging.WARNING)
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
        logging.getLogger('azure').setLevel(logging.WARNING)
        logging.getLogger('azure.core').setLevel(logging.WARNING)
        logging.getLogger('azure.ai').setLevel(logging.WARNING)
        
        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized. Log files: {self.log_dir}")


def setup_app_logging(log_dir: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Setup application logging (convenience function).
    
    Args:
        log_dir: Directory for log files. Defaults to 'logs' directory.
        level: Logging level (default: INFO)
    """
    config = LoggingConfig(log_dir)
    config.setup_logging(level)

