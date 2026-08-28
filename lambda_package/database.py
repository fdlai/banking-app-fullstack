"""Backward-compatible alias — canonical implementation lives in core/database.py.

Keeps a single Base/engine/SessionLocal instance shared by every module that
still does `from database import ...` instead of `from core.database import ...`.
"""

from core.database import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
