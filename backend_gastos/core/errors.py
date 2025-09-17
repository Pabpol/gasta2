"""
Custom exception classes and error handling utilities for the expense management system.
Provides structured error handling with appropriate HTTP status codes and user-friendly messages.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Standardized error codes for consistent error handling"""
    # Validation errors (400-499)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_DATE = "INVALID_DATE"
    INVALID_CATEGORY = "INVALID_CATEGORY"

    # Resource errors (400-499)
    EXPENSE_NOT_FOUND = "EXPENSE_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    BUDGET_NOT_FOUND = "BUDGET_NOT_FOUND"

    # Business logic errors (400-499)
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_PERIOD = "INVALID_PERIOD"

    # External service errors (500-599)
    TELEGRAM_ERROR = "TELEGRAM_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    CATEGORIZATION_ERROR = "CATEGORIZATION_ERROR"

    # System errors (500-599)
    DATABASE_ERROR = "DATABASE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ExpenseError(HTTPException):
    """Base exception class for expense management errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        self.user_message = user_message or message

        # Log the error with full context
        logger.error(
            f"{error_code.value}: {message}",
            extra={
                "error_code": error_code.value,
                "status_code": status_code,
                "details": self.details
            }
        )

        super().__init__(
            status_code=status_code,
            detail={
                "error": error_code.value,
                "message": self.user_message,
                "details": self.details
            }
        )

# Specific exception classes for different error types

class ValidationError(ExpenseError):
    """Validation errors (400)"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(error_code, message, status_code=400, details=details)

class NotFoundError(ExpenseError):
    """Resource not found errors (404)"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(error_code, message, status_code=404, details=details)

class ConflictError(ExpenseError):
    """Business logic conflicts (409)"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(error_code, message, status_code=409, details=details)

class ExternalServiceError(ExpenseError):
    """External service errors (502)"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(error_code, message, status_code=502, details=details)

class SystemError(ExpenseError):
    """Internal system errors (500)"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(error_code, message, status_code=500, details=details)

# Convenience functions for common errors

def invalid_input_error(field: str, value: Any, reason: str = "Invalid value") -> ValidationError:
    """Create a validation error for invalid input"""
    return ValidationError(
        ErrorCode.INVALID_INPUT,
        f"Invalid input for field '{field}': {reason}",
        details={"field": field, "value": value, "reason": reason}
    )

def expense_not_found_error(expense_id: str) -> NotFoundError:
    """Create an error for expense not found"""
    return NotFoundError(
        ErrorCode.EXPENSE_NOT_FOUND,
        f"Expense with ID '{expense_id}' not found",
        details={"expense_id": expense_id}
    )

def telegram_error(message: str, details: Optional[Dict] = None) -> ExternalServiceError:
    """Create a Telegram service error"""
    return ExternalServiceError(
        ErrorCode.TELEGRAM_ERROR,
        f"Telegram service error: {message}",
        details=details
    )

def storage_error(message: str, details: Optional[Dict] = None) -> SystemError:
    """Create a storage system error"""
    return SystemError(
        ErrorCode.STORAGE_ERROR,
        f"Storage system error: {message}",
        details=details
    )

def categorization_error(message: str, details: Optional[Dict] = None) -> SystemError:
    """Create a categorization error"""
    return SystemError(
        ErrorCode.CATEGORIZATION_ERROR,
        f"Categorization error: {message}",
        details=details
    )

# Error handling utilities

def handle_unexpected_error(error: Exception, context: str = "") -> SystemError:
    """Handle unexpected errors with proper logging and user-friendly message"""
    error_id = f"ERR_{hash(str(error)) % 10000:04d}"
    logger.error(
        f"Unexpected error in {context}: {str(error)}",
        exc_info=True,
        extra={"error_id": error_id, "context": context}
    )

    return SystemError(
        ErrorCode.INTERNAL_ERROR,
        "An unexpected error occurred. Please try again or contact support.",
        details={
            "error_id": error_id,
            "context": context,
            "type": type(error).__name__
        }
    )

def safe_execute(func, *args, context: str = "", **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except ExpenseError:
        # Re-raise our custom errors as-is
        raise
    except Exception as e:
        # Convert unexpected errors to system errors
        raise handle_unexpected_error(e, context)