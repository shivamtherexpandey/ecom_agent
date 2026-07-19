"""Shared types and helpers used by ecommerce agents."""

from __future__ import annotations

import inspect
import logging
import sys
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from configs.agents import DEFAULT_LLM_TEMPERATURE
from configs.configs import LOG_FORMAT, LOG_LEVEL, MAX_AGENT_ITERATIONS

logger = logging.getLogger("agentic_service")


class AgentState(TypedDict):
    user_query: str
    user_id: str = ""
    request_type: Literal["catalog", "order", "unknown"] = "unknown"
    tool_call_count: int = 0
    agent_response: str = ""
    response_data: List[Any] = []
    is_error: bool = False


class ToolCall(BaseModel):
    name: str = Field(description="Tool name to execute")
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the tool",
    )


class AgentDecision(BaseModel):
    agent_response: str = ""
    tool_call: Optional[ToolCall] = None


def build_tools_description(tools: Dict[str, Any]) -> str:
    descriptions = []

    for name, fn in tools.items():
        descriptions.append(
            f"{'=' * 70}\n"
            f"Tool: {name}\n"
            f"{'=' * 70}\n"
            f"{inspect.getdoc(fn)}"
        )

    return "\n\n".join(descriptions)


def build_chat_ollama(
    model_name: str,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
):
    return ChatOllama(
        model=model_name,
        temperature=temperature,
    )


def should_continue(state: Dict[str, Any]) -> str:
    if state["tool_call"] is None or state["iterations_count"] > MAX_AGENT_ITERATIONS:
        return "end"

    return "continue"


def empty_tool_result() -> Dict[str, Any]:
    return {
        "total": 0,
        "limit": 10,
        "offset": 0,
        "data": [],
    }
