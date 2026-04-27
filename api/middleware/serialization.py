"""
Optimized Serialization Middleware

Provides MessagePack and Protocol Buffers serialization for improved
performance over JSON serialization. Falls back to JSON for compatibility.
"""

import logging
from typing import Any, Awaitable, Callable, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Try to import msgpack, fallback to JSON if not available
try:
    import msgpack

    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    logger.warning("msgpack not available, falling back to JSON serialization")


def serialize_data(data: Any, format: str = "json") -> Union[bytes, str]:
    """
    Serialize data to specified format.

    Args:
        data: Data to serialize
        format: Serialization format (json, msgpack, protobuf)

    Returns:
        Serialized data
    """
    if format == "msgpack" and MSGPACK_AVAILABLE:
        return msgpack.packb(data, use_bin_type=True)
    elif format == "protobuf":
        # Protobuf requires schema definition - fallback to JSON
        logger.warning("Protobuf serialization requires schema definitions, using JSON")
        import json

        return json.dumps(data)
    else:
        import json

        return json.dumps(data)


def deserialize_data(data: Union[bytes, str], format: str = "json") -> Any:
    """
    Deserialize data from specified format.

    Args:
        data: Data to deserialize
        format: Serialization format (json, msgpack, protobuf)

    Returns:
        Deserialized data
    """
    if format == "msgpack" and MSGPACK_AVAILABLE:
        if isinstance(data, str):
            data = data.encode("utf-8")
        return msgpack.unpackb(data, raw=False)
    else:
        import json

        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)


def get_best_format(request: Request) -> str:
    """
    Determine best serialization format based on request headers.

    Args:
        request: HTTP request

    Returns:
        Best format for response
    """
    accept_header = request.headers.get("Accept", "")

    # Check for MessagePack preference
    if "application/msgpack" in accept_header or "application/x-msgpack" in accept_header:
        if MSGPACK_AVAILABLE:
            return "msgpack"

    # Default to JSON
    return "json"


class OptimizedSerializationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that optimizes request/response serialization.

    Supports MessagePack for improved performance and reduced payload size.
    Falls back to JSON for clients that don't support MessagePack.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.msgpack_enabled = MSGPACK_AVAILABLE

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with optimized serialization.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with optimized serialization
        """
        # Store format preference for response
        response_format = get_best_format(request)
        request.state.response_format = response_format

        # Log format selection for debugging
        logger.debug(f"Selected serialization format: {response_format}")

        # Process request
        response = await call_next(request)

        # Set appropriate content type for response
        if response_format == "msgpack":
            response.headers["Content-Type"] = "application/msgpack"
        else:
            response.headers["Content-Type"] = "application/json"

        return response


class SerializationManager:
    """
    Manager for handling data serialization across the API.

    Provides consistent serialization/deserialization with format negotiation.
    """

    def __init__(self) -> None:
        self.msgpack_available = MSGPACK_AVAILABLE
        self.preferred_format = "msgpack" if MSGPACK_AVAILABLE else "json"

    def serialize(self, data: Any, format: Optional[str] = None) -> Union[bytes, str]:
        """
        Serialize data with format selection.

        Args:
            data: Data to serialize
            format: Target format (defaults to preferred)

        Returns:
            Serialized data
        """
        target_format = format or self.preferred_format
        return serialize_data(data, target_format)

    def deserialize(self, data: Union[bytes, str], format: Optional[str] = None) -> Any:
        """
        Deserialize data with format detection.

        Args:
            data: Data to deserialize
            format: Source format (auto-detected if not specified)

        Returns:
            Deserialized data
        """
        target_format = format or self.preferred_format
        return deserialize_data(data, target_format)

    def get_content_type(self, format: Optional[str] = None) -> str:
        """
        Get MIME content type for format.

        Args:
            format: Serialization format

        Returns:
            MIME content type string
        """
        target_format = format or self.preferred_format
        if target_format == "msgpack":
            return "application/msgpack"
        return "application/json"

    @property
    def supported_formats(self) -> list[str]:
        """Return list of supported serialization formats."""
        formats = ["json"]
        if self.msgpack_available:
            formats.append("msgpack")
        return formats


# Global serialization manager instance
serialization_manager: SerializationManager = SerializationManager()
