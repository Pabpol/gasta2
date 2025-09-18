"""
Enhanced logging configuration for the expense management system.
Provides structured logging with request tracking, performance monitoring, and error correlation.
"""
import logging
import logging.handlers
import sys
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
import uuid

from .paths import DATA_DIR

# Create logs directory
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class RequestIdFilter(logging.Filter):
    """Filter to add request ID to all log records"""

    def __init__(self, request_id: Optional[str] = None):
        super().__init__()
        self.request_id = request_id or str(uuid.uuid4())

    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = self.request_id
        return True

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def format(self, record):
        # Create base log entry
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request_id if available (safely)
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        else:
            log_entry["request_id"] = "N/A"

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add common fields safely
        for field in ['user_id', 'expense_id', 'category', 'amount', 'error_code', 'status_code']:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        return json.dumps(log_entry, ensure_ascii=False)

class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""

    def __init__(self):
        super().__init__()
        self.start_times = {}

    def filter(self, record):
        if hasattr(record, 'request_id'):
            request_id = record.request_id
            if record.getMessage().startswith("Request started"):
                self.start_times[request_id] = time.time()
            elif record.getMessage().startswith("Request completed"):
                start_time = self.start_times.get(request_id)
                if start_time:
                    duration = time.time() - start_time
                    record.duration_ms = round(duration * 1000, 2)
                    del self.start_times[request_id]
        return True

def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    structured: bool = False
) -> logging.Logger:
    """
    Set up comprehensive logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        structured: Whether to use structured JSON logging
    """

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Create formatters
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
            defaults={'request_id': 'N/A'}
        )

    handlers = []

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(PerformanceFilter())
        handlers.append(console_handler)

    # File handler
    if log_to_file:
        # Main log file
        log_file = LOGS_DIR / "app.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(PerformanceFilter())
        handlers.append(file_handler)

        # Error log file (WARNING and above)
        error_log_file = LOGS_DIR / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file, maxBytes=10*1024*1024, backupCount=5
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        handlers.append(error_handler)

    # Add handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)

    # Create main logger
    logger = logging.getLogger("expense_manager")
    logger.info("Logging system initialized", extra={"level": level, "structured": structured})

    return logger

def get_request_logger(request_id: str, user_id: Optional[str] = None) -> logging.LoggerAdapter:
    """Get a logger adapter with request context"""
    logger = logging.getLogger("expense_manager.request")

    # Create adapter with context
    context = {"request_id": request_id}
    if user_id:
        context["user_id"] = user_id

    return logging.LoggerAdapter(logger, context)

def log_request_start(logger: logging.LoggerAdapter, method: str, path: str, query_params: Optional[Dict] = None):
    """Log the start of a request"""
    message = f"Request started: {method} {path}"
    extra = {}
    if query_params:
        extra["query_params"] = query_params
    logger.info(message, extra=extra)

def log_request_end(logger: logging.LoggerAdapter, status_code: int, duration_ms: Optional[float] = None):
    """Log the end of a request"""
    message = f"Request completed with status {status_code}"
    extra = {"status_code": status_code}
    if duration_ms:
        extra["duration_ms"] = duration_ms
    logger.info(message, extra=extra)

def log_error(logger: logging.LoggerAdapter, error: Exception, error_code: Optional[str] = None, context: Optional[Dict] = None):
    """Log an error with full context"""
    message = f"Error occurred: {str(error)}"
    extra = {"error_type": type(error).__name__}
    if error_code:
        extra["error_code"] = error_code
    if context:
        extra.update(context)
    logger.error(message, exc_info=True, extra=extra)

def log_business_event(logger: logging.LoggerAdapter, event: str, details: Dict[str, Any]):
    """Log business events (expense created, category changed, etc.)"""
    logger.info(f"Business event: {event}", extra={"event": event, **details})

def get_request_logger_from_request(request) -> logging.LoggerAdapter:
    """Get a request-scoped logger from a FastAPI request object"""
    # Extract request ID from request scope (set by middleware)
    request_id = getattr(request.scope, 'request_id', 'unknown')
    return get_request_logger(request_id)

# Global logger instance
main_logger = setup_logging()