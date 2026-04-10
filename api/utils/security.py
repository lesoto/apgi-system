"""
Security utilities for API protection.
"""

import socket
import ipaddress
from urllib.parse import urlparse
from typing import Optional


def is_safe_url(url: str, allowed_schemes: Optional[list[str]] = None) -> bool:
    """
    Check if a URL is safe for server-side requests (SSRF protection).

    Checks that the URL uses allowed schemes and does not point to
    private, loopback, or reserved IP addresses.
    """
    if not url:
        return False

    if allowed_schemes is None:
        allowed_schemes = ["https"]  # Default to secure only

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in allowed_schemes:
            return False

        # Check hostname
        hostname = parsed.hostname
        if not hostname:
            return False

        # Resolve hostname to IP
        try:
            ip_address = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_address)

            # Check if IP is private, lookback, or reserved
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                return False

            # Check for Link-Local (like AWS metadata service 169.254.169.254)
            if ip.is_link_local:
                return False

            return True
        except (socket.gaierror, ValueError):
            # Portally it's an invalid hostname or can't be resolved
            return False

    except Exception:
        return False
