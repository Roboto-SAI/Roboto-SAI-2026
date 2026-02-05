from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
import json
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.grok_client import get_grok_client

router = APIRouter()


class ToolRequest(BaseModel):
    serverId: Optional[str] = Field(
        default=None,
        description="Optional MCP server identifier; defaults to the filesystem server."
    )
    toolName: str
    description: Optional[str] = None
    args: Dict[str, Any] = Field(default_factory=dict)


class ChatEvent(BaseModel):
    id: str
    timestamp: int
    type: str
    data: Dict[str, Any]


class ChatRequest(BaseModel):
    message: str
    reasoning_effort: Optional[str] = Field(default="medium")
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None  # For memory integration
    session_id: Optional[str] = None  # For conversation continuity
    tool_request: Optional[ToolRequest] = None


class ChatResponse(BaseModel):
    reply: str
    reasoning_trace_id: Optional[str] = None
    tokens_used: Optional[int] = None
    mode: Optional[str] = "entangled"
    events: List[ChatEvent] = Field(default_factory=list)


def _current_millis() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _create_event(event_type: str, data: Dict[str, Any]) -> ChatEvent:
    return ChatEvent(
        id=str(uuid4()),
        timestamp=_current_millis(),
        type=event_type,
        data=data,
    )


def _extract_path(message: str) -> Optional[str]:
    match = re.search(r"[A-Za-z]:\\[^,;\n]+", message)
    if match:
        return match.group(0)
    return None


def _parse_inline_tool_request(message: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"```tool_request\s*\n([\s\S]+?)\n```", message, flags=re.IGNORECASE)
    if not match:
        return None
    payload = match.group(1).strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _context_tool_request(context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not context:
        return None
    for key in ("tool_request", "toolCall", "mcp_tool", "mcp_tool_call"):
        candidate = context.get(key)
        if isinstance(candidate, dict) and candidate.get("toolName"):
            return candidate
    return None


def _match_heuristic(message: str) -> Optional[ToolRequest]:
    normalized = message.lower()
    path = _extract_path(message)
    if not path:
        path = "D:\\temp.txt"

    if any(phrase in normalized for phrase in ["write file", "save file", "create file"]):
        return ToolRequest(
            serverId="filesystem",
            toolName="fs_writeFile",
            description="Write a file using MCP",
            args={
                "path": path,
                "content": message,
                "createDirs": True,
            },
        )

    if any(phrase in normalized for phrase in ["read file", "open file", "show file"]):
        return ToolRequest(
            serverId="filesystem",
            toolName="fs_readFile",
            description="Read a file via MCP",
            args={
                "path": path,
                "encoding": "utf-8",
            },
        )

    if any(phrase in normalized for phrase in ["list directory", "list files", "show folder"]):
        directory = path if path and path.endswith("\\") else (path + "\\" if path else "D:\\")
        return ToolRequest(
            serverId="filesystem",
            toolName="fs_listDir",
            description="List directory contents",
            args={
                "path": directory,
            },
        )

    if "tweet" in normalized and any(phrase in normalized for phrase in ["post", "publish"]):
        return ToolRequest(
            serverId="twitter",
            toolName="twitter_postTweet",
            description="Post to Twitter via MCP",
            args={
                "content": message,
            },
        )

    if "email" in normalized and "send" in normalized:
        return ToolRequest(
            serverId="email",
            toolName="email_sendEmail",
            description="Send email via MCP",
            args={
                "to": "demo@example.com",
                "subject": "Requested via Roboto SAI",
                "body": message,
            },
        )

    return None


def _build_tool_request(req: ChatRequest) -> Optional[ToolRequest]:
    explicit = req.tool_request
    if explicit:
        return explicit

    inline = _parse_inline_tool_request(req.message)
    if inline:
        try:
            return ToolRequest(**inline)
        except Exception:  # pragma: no cover - best effort
            pass

    context_request = _context_tool_request(req.context)
    if context_request:
        try:
            return ToolRequest(**context_request)
        except Exception:
            pass

    return _match_heuristic(req.message)


def _build_tool_event(tool_request: ToolRequest) -> ChatEvent:
    data = {
        "id": str(uuid4()),
        "source": "backend",
        "serverId": tool_request.serverId or "filesystem",
        "toolName": tool_request.toolName,
        "description": tool_request.description or "Requires MCP execution",
        "args": tool_request.args,
    }
    return _create_event("tool_call", data)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    grok = Depends(get_grok_client),
):
    reply, meta = await grok.chat(
        message=req.message,
        reasoning_effort=req.reasoning_effort,
        context=req.context or {},
        user_id=req.user_id,
        session_id=req.session_id,
    )

    assistant_event = _create_event("assistant_message", {
        "content": reply,
        "metadata": {
            "reasoning_trace_id": meta.get("trace_id"),
            "mode": meta.get("mode"),
            "elapsed": meta.get("elapsed"),
        },
    })

    events = [assistant_event]
    tool_request = _build_tool_request(req)
    if tool_request:
        events.append(_build_tool_event(tool_request))

    return ChatResponse(
        reply=reply,
        reasoning_trace_id=meta.get("trace_id"),
        tokens_used=meta.get("tokens_used"),
        mode=meta.get("mode", "entangled"),
        events=events,
    )
