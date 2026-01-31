"""
MCP Router - Secured endpoints for MCP configuration management.
All endpoints require authentication.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional
import json
import os
import shutil
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

MCP_CONFIG_PATH = os.path.join(os.getcwd(), ".vscode", "mcp.json")

# Maximum config size to prevent DoS (100KB)
MAX_CONFIG_SIZE = 100 * 1024

# Allowed URL schemes
ALLOWED_URL_SCHEMES = ["http", "https"]


class MCPServerConfig(BaseModel):
    command: Optional[str] = None
    args: Optional[List[str]] = None
    type: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    env: Optional[Dict[str, str]] = None
    disabled: Optional[bool] = False

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validate URL scheme
        if not any(v.startswith(f"{scheme}://") for scheme in ALLOWED_URL_SCHEMES):
            raise ValueError(f"URL must use one of the allowed schemes: {ALLOWED_URL_SCHEMES}")
        return v

    @field_validator('command')
    @classmethod
    def validate_command(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Prevent shell injection - only allow alphanumeric, dash, underscore, dot, slash
        if not re.match(r'^[\w\-./]+$', v):
            raise ValueError("Command contains invalid characters")
        # Block suspicious patterns
        dangerous_patterns = ['../', '~/', '$', '`', '|', ';', '&&', '||']
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"Command contains forbidden pattern: {pattern}")
        return v

    @field_validator('args')
    @classmethod
    def validate_args(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        # Validate each argument
        dangerous_patterns = ['$', '`', '|', ';', '&&', '||', '$(', '${']
        for arg in v:
            for pattern in dangerous_patterns:
                if pattern in arg:
                    raise ValueError(f"Argument contains forbidden pattern: {pattern}")
        return v


class MCPConfig(BaseModel):
    mcpServers: Dict[str, MCPServerConfig]


# Import auth dependency - use a lazy import to avoid circular imports
def get_current_user_dependency():
    """Get the current user authentication dependency."""
    from .main import get_current_user
    return get_current_user


@router.get("/api/mcp/config", tags=["MCP"])
async def get_mcp_config(request: Request):
    """Get current MCP configuration. Requires authentication."""
    # Authenticate user
    get_current_user = get_current_user_dependency()
    try:
        user = await get_current_user(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not os.path.exists(MCP_CONFIG_PATH):
        return {"mcpServers": {}}
    try:
        with open(MCP_CONFIG_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in MCP config file")
        raise HTTPException(status_code=500, detail="Configuration file is corrupted")
    except Exception as e:
        logger.error(f"Failed to read MCP config: {e}")
        raise HTTPException(status_code=500, detail="Failed to read configuration")


@router.post("/api/mcp/config", tags=["MCP"])
async def update_mcp_config(config: MCPConfig, request: Request):
    """Update MCP configuration. Requires authentication."""
    # Authenticate user
    get_current_user = get_current_user_dependency()
    try:
        user = await get_current_user(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Validate config size
        config_json = config.model_dump_json()
        if len(config_json) > MAX_CONFIG_SIZE:
            raise HTTPException(status_code=400, detail="Configuration too large")

        # Ensure directory exists
        config_dir = os.path.dirname(MCP_CONFIG_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        # Backup existing config
        if os.path.exists(MCP_CONFIG_PATH):
            shutil.copy2(MCP_CONFIG_PATH, MCP_CONFIG_PATH + ".bak")

        with open(MCP_CONFIG_PATH, "w") as f:
            json.dump(config.model_dump(), f, indent=4)
        
        logger.info(f"MCP config updated by user {user.get('id', 'unknown')}")
        return {"status": "success", "message": "Config updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update MCP config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.post("/api/mcp/restart", tags=["MCP"])
async def restart_mcp_services(request: Request):
    """Restart MCP services. Requires authentication."""
    # Authenticate user
    get_current_user = get_current_user_dependency()
    try:
        user = await get_current_user(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required")

    logger.info(f"MCP services restart requested by user {user.get('id', 'unknown')}")
    # Implementation depends on how MCP servers are run.
    # If run as subprocesses, we would kill and restart them here.
    return {"status": "success", "message": "MCP services restarted (simulated)"}