"""
EvOLve Security Hardening — dashboard/backend/middleware/audit.py
Audit and Request Logging Middleware.
Records structured audit logs containing timestamp, client IP, HTTP method,
route, status code, and response latency in milliseconds to fulfill compliance
and forensic monitoring requirements.
"""

import time
import logging
from datetime import datetime, timezone
from collections import deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure structured audit logger
audit_logger = logging.getLogger("evolve.audit")
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [AUDIT_LOG] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)
    audit_logger.setLevel(logging.INFO)

# In-memory buffer for the last 100 audit events for compliance & monitoring review
AUDIT_LOG_BUFFER = deque(maxlen=100)


def get_client_ip(request: Request) -> str:
    """Extract client IP respecting potential reverse proxies."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures and logs audit telemetry for every incoming request.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        timestamp_iso = datetime.now(timezone.utc).isoformat()
        client_ip = get_client_ip(request)
        method = request.method
        route = request.url.path

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            audit_logger.error(
                f"timestamp={timestamp_iso} client_ip={client_ip} method={method} "
                f"route={route} status=500 latency_ms={duration_ms} error={str(exc)}"
            )
            AUDIT_LOG_BUFFER.append({
                "timestamp": timestamp_iso,
                "client_ip": client_ip,
                "method": method,
                "route": route,
                "status_code": 500,
                "latency_ms": duration_ms,
                "error": str(exc),
            })
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Log formatted audit line
        audit_logger.info(
            f"timestamp={timestamp_iso} client_ip={client_ip} method={method} "
            f"route={route} status={status_code} latency_ms={duration_ms}"
        )

        # Append structured entry to compliance buffer
        AUDIT_LOG_BUFFER.append({
            "timestamp": timestamp_iso,
            "client_ip": client_ip,
            "method": method,
            "route": route,
            "status_code": status_code,
            "latency_ms": duration_ms,
        })

        # Append server timing header for transparent observability
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        return response
