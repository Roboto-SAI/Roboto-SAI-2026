"""
Database setup for Roboto SAI backend (SQLite + SQLAlchemy async).
"""

import os
import logging
from typing import AsyncGenerator
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Ensure Supabase tables exist (idempotent)."""
    supabase = get_supabase_client()
    if supabase is None:
        logger.warning("No Supabase client; skipping init_db")
        return
    
    # Verify tables (select-only, no RLS/perm issues)
    tables = [
        "users",
        "auth_sessions", 
        "magic_link_tokens",
        "messages",
        "message_feedback"
    ]
    
    for table in tables:
        try:
            supabase.table(table).select("id", head=True).limit(1).execute()
            logger.info(f"Verified table: {table}")
        except Exception as e:
            logger.warning(f"Table {table} verify failed: {e}")
    
    logger.info("Supabase tables verified")


from utils.supabase_client import get_supabase_client
