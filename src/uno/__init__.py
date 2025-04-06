"""
Uno - Microservices micro-framework for NATS
"""
from .core import (
    Service,
    Client,
    Handler,
    Endpoint,
    RequestError,
    start_nats_service
)

__version__ = "0.1.0"