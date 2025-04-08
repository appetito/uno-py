"""
Uno - Microservices micro-framework for NATS
"""
from .core import (
    Service,
    Client,
    handler,
    RequestError,
    start_nats_service
)

__version__ = "0.1.0"