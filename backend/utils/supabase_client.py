import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Get Supabase client. Prefer SERVICE_ROLE_KEY; fallback to ANON_KEY on auth failure."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        logger.warning("No SUPABASE_URL")
        return None

    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    # Try service role first
    if service_role_key:
        try:
            client = create_client(url, service_role_key)
            # Quick test: query users count (head=True avoids data)
            client.table("users").select("count", count="exact", head=True).execute()
            logger.info("Supabase client using service_role_key")
            return client
        except Exception as e:
            logger.warning(f"Service role invalid ({str(e)}) - falling back to anon")

    # Fallback to anon
    if anon_key:
        try:
            client = create_client(url, anon_key)
            logger.info("Supabase client using anon_key")
            return client
        except Exception as e:
            logger.error(f"Anon key invalid: {str(e)}")
            return None

    logger.warning("No valid Supabase keys found")
    return None