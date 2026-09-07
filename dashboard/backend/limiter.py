"""
EvOLve Security Hardening — dashboard/backend/limiter.py
Centralized SlowAPI rate limiter configuration.
Provides IP-based throttling to defend against Denial-of-Service (DoS) and API abuse.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared Limiter instance using client remote IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
