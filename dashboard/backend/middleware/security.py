"""
EvOLve Security Hardening — dashboard/backend/middleware/security.py
Adds robust security response headers to all outgoing HTTP responses to protect
against clickjacking, MIME-sniffing, XSS, and insecure transport vulnerabilities.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects defense-in-depth security headers into all HTTP responses.
    Complies with OWASP Secure Headers Project standards.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent browser from MIME-sniffing the response content-type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by forbidding embedding in iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Enforce strict HTTPS communication for 1 year, including subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (CSP) to restrict resource loading origins
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https: blob:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https://earthengine.googleapis.com; "
            "frame-ancestors 'none';"
        )

        # Referrer policy to prevent information leakage across origins
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Legacy XSS protection filter for supported browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Restrict sensitive browser APIs
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        return response
