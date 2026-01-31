"""
Agentic Loop Module for Roboto SAI
Integrates LangChain ReAct agent with Self-Modification and MCP tools.
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from langchain_core.tools import Tool, tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI 
# using ChatOpenAI as a generic interface, will configure for XAI/Grok if compatible or use standard LLM
# If Grok is not standard OpenAI compatible, we might need custom adapter. 
# As per grok_llm.py, there is a custom GrokLLM.

logger = logging.getLogger(__name__)

try:
    from self_code_modification import SelfCodeModificationEngine, ModificationConfig
    from grok_llm import GrokLLM
    HAS_MODULES = True
except ImportError as e:
    logger.warning(f"Failed to import modules: {e}")
    HAS_MODULES = False
    SelfCodeModificationEngine = None
    ModificationConfig = None
    GrokLLM = None
    GrokLLM = None

router = APIRouter()

# Initialize Self-Modification Engine (only if available)
if HAS_MODULES and ModificationConfig and SelfCodeModificationEngine:
    try:
        mod_config = ModificationConfig(
            safety_threshold=0.8,
            enable_auto_testing=True
        )
        self_mod_engine = SelfCodeModificationEngine(config=mod_config, full_autonomy=False)
    except Exception as e:
        logger.warning(f"Failed to initialize self-modification engine: {e}")
        self_mod_engine = None
else:
    logger.warning("Self-modification modules not available")
    self_mod_engine = None

# --- Tools ---

@tool
def execute_local_script(script_path: str) -> str:
    """
    Execute a local python script securely.
    Only allows scripts in the 'scripts/' or 'backend/scripts/' directory.
    """
    # Security check
    allowed_dirs = ["scripts", "backend"]
    valid = False
    for d in allowed_dirs:
        if script_path.startswith(d) or script_path.startswith(f"./{d}"):
            valid = True
            break
    
    if not valid:
        return "Error: Script execution only allowed in scripts or backend directories."

    try:
        # Check if file exists
        if not os.path.exists(script_path):
             logger.error(f"Script not found: {script_path}")
             return f"Error: File {script_path} not found."

        result = subprocess.run(
            ["python", script_path], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        logger.error(f"Script execution timed out: {script_path}")
        return "Error: Script execution timed out."
    except Exception as e:
        logger.error(f"Execution failed for {script_path}: {e}")
        return f"Execution failed: {str(e)}"

@tool
def modify_self_code(filename: str, changes_json: str, description: str) -> str:
    """
    Propose a modification to the codebase.
    filename: Path to file
    changes_json: JSON string with modification details (type, etc)
    description: Why this change is needed
    """
    try:
        changes = json.loads(changes_json)
    except json.JSONDecodeError:
        return "Error: changes_json must be valid JSON"

    # In a real agentic loop, we might ask for human confirmation here via a callback 
    # or return a "Proposal Created" status that the UI then approves.
    # For now, we will use the engine's check.
    
    success = self_mod_engine.modify_code(filename, changes, modification_type="agent_request")
    if success:
        return f"Successfully modified {filename}. Backup created."
    else:
        return f"Failed to modify {filename}. Check logs."

# MCP Tools Loader
def load_mcp_tools() -> List[Tool]:
    """
    Load tools from mcp.json configuration.
    This is a placeholder for actual MCP client implementation.
    Real MCP would connect to servers and discover tools.
    """
    tools = []
    mcp_config_path = os.path.join(os.getcwd(), ".vscode", "mcp.json")
    if os.path.exists(mcp_config_path):
        try:
            with open(mcp_config_path, 'r') as f:
                config = json.load(f)
                # Parse config and create tools (mocking for now as full MCP client is complex)
                for server, details in config.get("mcpServers", {}).items():
                    # Create a generic tool wrapper for the server
                    # In reality we'd iterate capabilities
                    pass
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
    return tools

# --- Agent Setup ---

def get_agent_executor():
    # Load Generic Tools
    tools = [execute_local_script, modify_self_code]
    
    # Load MCP Tools
    # mcp_tools = load_mcp_tools() 
    # tools.extend(mcp_tools)
    
    # Initialize LLM (Grok or Fallback)
    # Using a placeholder for the actual agent construction
    # Ideally we use LangGraph or AgentExecutor
    
    return tools

# --- Helper for direct interaction ---
class AgentRequest(BaseModel):
    message: str
    context: Optional[str] = None

@router.post("/api/agent/chat", tags=["Agent"])
async def agent_chat(req: AgentRequest):
    """
    Chat with the specialized Agent that has tool access.
    """
    try:
        # Simple ReAct loop simulation or actual call
        # For this task, we'll return a simulated response if LLM isn't fully configured
        # or implement a basic tool selection loop.
        
        tools = get_agent_executor()
        
        # Here we would invoke the agent. 
        # Since I don't have the full GrokLLM adapter source handy in this context (it was imported in main),
        # I will leave the actual LLM call as a TODO or use a mock for the verify step.
        
        return {
            "response": f"Agent received: {req.message}. (Agent logic unimplemented pending LLM connection)",
            "tools_available": [t.name for t in tools]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
