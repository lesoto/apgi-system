"""
Exception Handlers for APGI API

Global exception handlers for consistent error responses across the API.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import uuid
from typing import Union

from api.exceptions import APIError


logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracking.
    
    Returns:
        Unique request ID string
    """
    return f"req_{uuid.uuid4().hex[:12]}"


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle custom APIError exceptions.
    
    Logs the error and returns a consistent JSON error response.
    
    Args:
        request: The FastAPI request object
        exc: The APIError exception
        
    Returns:
        JSONResponse with error details
    """
    # Get or generate request ID
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Log error with context
    logger.error(
        f"API Error: {exc.code}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        },
        exc_info=True
    )
    
    # Return error response
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(request_id=request_id)
    )


async def validation_error_handler(
    request: Request,
    exc: Union[RequestValidationError, PydanticValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Transforms Pydantic validation errors into consistent API error responses.
    
    Args:
        request: The FastAPI request object
        exc: The validation error exception
        
    Returns:
        JSONResponse with validation error details
    """
    # Get or generate request ID
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log validation error
    logger.warning(
        "Request validation failed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "validation_errors": errors
        }
    )
    
    # Return validation error response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "request_id": request_id,
                "timestamp": None,  # Will be set by middleware if available
                "details": {"validation_errors": errors}
            }
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle standard HTTP exceptions.
    
    Converts Starlette/FastAPI HTTPException to consistent error format.
    
    Args:
        request: The FastAPI request object
        exc: The HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    # Get or generate request ID
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Map status code to error code
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    # Log HTTP exception
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(
        log_level,
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": str(exc.detail),
                "request_id": request_id,
                "timestamp": None,  # Will be set by middleware if available
                "details": {}
            }
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Catches all unhandled exceptions and returns a 500 error response.
    Logs full stack trace for debugging.
    
    Args:
        request: The FastAPI request object
        exc: The unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    # Get or generate request ID
    request_id = getattr(request.state, "request_id", generate_request_id())
    
    # Generate unique error ID for tracking
    error_id = f"err_{uuid.uuid4().hex[:12]}"
    
    # Log unexpected error with full stack trace
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "error_id": error_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    )
    
    # Return generic error response (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
                "timestamp": None,  # Will be set by middleware if available
                "details": {
                    "error_id": error_id
                }
            }
        }
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    This should be called during application initialization to set up
    global exception handling.
    
    Args:
        app: The FastAPI application instance
    """
    # Custom API errors
    app.add_exception_handler(APIError, api_error_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(PydanticValidationError, validation_error_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)
    
    logger.info("Exception handlers registered successfully")
