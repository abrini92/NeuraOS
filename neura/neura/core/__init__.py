"""
Core module - Central API, event bus, types, and configuration.

This module provides the foundational components that all other modules
communicate through. No module should directly import another; instead,
all communication happens via:
- REST API (localhost)
- Event Bus (pub/sub)
"""

from neura.core.exceptions import CoreError, NeuraError
from neura.core.types import Event, Result

__all__ = ["NeuraError", "CoreError", "Result", "Event"]
