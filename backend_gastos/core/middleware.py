"""
FastAPI middleware for request tracking, logging, and error handling.
Provides comprehensive request lifecycle management for the expense management system.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

from .logging_config import get_request_logger, log_request_start, log_request_end, log_error
from .errors import handle_unexpected_error, ExpenseError

logger = logging.getLogger(__name__)

class RequestTrackingMiddleware:
    """Middleware for tracking requests with unique IDs and performance monitoring"""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to scope for use in handlers
        scope["request_id"] = request_id

        # Track request start
        start_time = time.time()

        # Create request logger
        request_logger = get_request_logger(request_id)

        async def send_with_logging(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time
                duration_ms = round(duration * 1000, 2)

                # Log request completion
                log_request_end(request_logger, status_code, duration_ms)

                # Add performance headers
                if "headers" not in message:
                    message["headers"] = []
                message["headers"].extend([
                    [b"X-Request-ID", request_id.encode()],
                    [b"X-Response-Time", f"{duration_ms}ms".encode()],
                ])

            await send(message)

        # Extract request info for logging
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "UNKNOWN")
        query_string = scope.get("query_string", b"").decode()

        # Parse query parameters for logging
        query_params = {}
        if query_string:
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    query_params[key] = value

        # Log request start
        log_request_start(request_logger, method, path, query_params if query_params else None)

        try:
            # Process the request
            await self.app(scope, receive, send_with_logging)
        except Exception as e:
            # Handle unexpected errors
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)

            # Log the error
            log_error(request_logger, e, context={
                "method": method,
                "path": path,
                "duration_ms": duration_ms
            })

            # Convert to proper error response
            if isinstance(e, ExpenseError):
                # Our custom errors are already properly formatted
                error_response = JSONResponse(
                    status_code=e.status_code,
                    content=e.detail
                )
            else:
                # Handle unexpected errors
                system_error = handle_unexpected_error(e, f"{method} {path}")
                error_response = JSONResponse(
                    status_code=system_error.status_code,
                    content=system_error.detail
                )

            # Add tracking headers to error response
            error_response.headers["X-Request-ID"] = request_id
            error_response.headers["X-Response-Time"] = f"{duration_ms}ms"

            # Send error response
            await send_with_logging({
                "type": "http.response.start",
                "status": error_response.status_code,
                "headers": [
                    [key.encode(), value.encode()] for key, value in error_response.headers.items()
                ]
            })

            # Send response body
            body = error_response.body
            await send_with_logging({
                "type": "http.response.body",
                "body": body
            })

class HealthCheckMiddleware:
    """Middleware to add health check headers to all responses"""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Add health headers to all responses
        async def send_with_health_headers(message):
            if message["type"] == "http.response.start":
                if "headers" not in message:
                    message["headers"] = []
                # Add server health indicator
                message["headers"].append([b"X-Server-Healthy", b"true"])
            await send(message)

        await self.app(scope, receive, send_with_health_headers)

# Request context utilities
def get_request_id(request: Request) -> str:
    """Get the request ID from the request scope"""
    return getattr(request.scope, 'request_id', 'unknown')

def get_request_logger_from_request(request: Request) -> logging.LoggerAdapter:
    """Get a request-scoped logger from the FastAPI request object"""
    request_id = get_request_id(request)
    return get_request_logger(request_id)