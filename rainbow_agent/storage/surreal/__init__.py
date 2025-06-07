"""
SurrealDB client modules for Rainbow Agent.

This package contains the unified SurrealDB client:
- unified_client.py: Unified client using official SurrealDB library
"""

from .unified_client import UnifiedSurrealClient

__all__ = ['UnifiedSurrealClient']
