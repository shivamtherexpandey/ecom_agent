"""Catalog agent package with tools, service client, and LangGraph workflow."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from langsmith import traceable

from agents.catalog_agent.service import CatalogService
from agents.catalog_agent.tools import AgenticCatalogTools
from agents.common import (
    AgentDecision,
    AgentState,
    ToolCall,
    build_chat_ollama,
    build_tools_description,
    empty_tool_result,
    logger,
    should_continue,
)
from configs.agents import (
    CATALOG_AGENT_MODEL,
    CATALOG_PLANNER_SYSTEM_PROMPT,
)


class CatalogSubAgentState(TypedDict):
    user_query: str
    past_calls_history: List[Dict[str, Any]]
    tool_call: Optional[ToolCall]
    agent_response: Optional[str]
    products: Dict[str, Any]
    products_found: bool
    iterations_count: int


agentic_catalog_service = AgenticCatalogTools()
CATALOG_TOOLS = {
    "search_products": agentic_catalog_service.search_products,
}
CATALOG_TOOLS_DESCRIPTION = build_tools_description(CATALOG_TOOLS)

parser = PydanticOutputParser(pydantic_object=AgentDecision)
format_instructions = parser.get_format_instructions()

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            CATALOG_PLANNER_SYSTEM_PROMPT,
        ),
        (
            "user",
            """
User Query:
{user_query}

Past History:
{history}
""",
        ),
    ]
)

@traceable
def planner_node(state: CatalogSubAgentState) -> CatalogSubAgentState:
    logger.info("=" * 80)
    logger.info("CATALOG PLANNER NODE")
    logger.info("=" * 80)

    history = json.dumps(state["past_calls_history"], indent=2, ensure_ascii=False)
    categories = agentic_catalog_service.fetch_categories()
    prompt = planner_prompt.format(
        user_query=state["user_query"],
        history=history,
        tools_desc=CATALOG_TOOLS_DESCRIPTION,
        format_instructions=format_instructions,
        categories=categories,
    )

    llm = build_chat_ollama(CATALOG_AGENT_MODEL)
    response = llm.with_structured_output(AgentDecision).invoke(prompt)

    logger.info("Planner Response: %s", response)

    return {
        **state,
        "agent_response": response.agent_response,
        "tool_call": response.tool_call,
        "iterations_count": state["iterations_count"] + 1,
        "products": state["products"],
    }


@traceable
def tool_executor_node(state: CatalogSubAgentState) -> CatalogSubAgentState:
    logger.info("=" * 80)
    logger.info("CATALOG TOOL EXECUTOR")
    logger.info("=" * 80)

    tool_call = state["tool_call"]

    if tool_call is None:
        products = state.get("products", empty_tool_result())
        return {
            **state,
            "products_found": bool(products.get("data")),
        }

    tool_name = tool_call.name
    args = tool_call.args or {}
    tool_fn = CATALOG_TOOLS.get(tool_name)

    if tool_fn is None:
        logger.error("Tool '%s' not found.", tool_name)
        tool_result = empty_tool_result()
    else:
        try:
            tool_result = tool_fn(**args)
            logger.info("Tool executed successfully.")
        except Exception:
            logger.exception("Tool execution failed.")
            tool_result = empty_tool_result()

    history_entry = {
        "tool": tool_name,
        "args": args,
        "success": bool(tool_result.get("data")),
        "result": tool_result,
    }

    return {
        **state,
        "past_calls_history": state["past_calls_history"] + [history_entry],
        "products": tool_result,
        "tool_call": None,
    }


def build_catalog_app():
    graph = StateGraph(CatalogSubAgentState)
    graph.add_node("planner", planner_node)
    graph.add_node("tool", tool_executor_node)
    graph.set_entry_point("planner")
    graph.add_conditional_edges(
        "planner",
        should_continue,
        {
            "continue": "tool",
            "end": END,
        },
    )
    graph.add_edge("tool", "planner")
    return graph.compile()


catalog_app = build_catalog_app()


def catalog_agent_node(state: AgentState) -> AgentState:
    result = catalog_app.invoke(
        {
            "user_query": state["user_query"],
            "past_calls_history": [],
            "tool_call": None,
            "agent_response": None,
            "products": empty_tool_result(),
            "products_found": False,
            "iterations_count": 0,
        }
    )

    products = result.get("products") or empty_tool_result()

    return {
        **state,
        "agent_response": result["agent_response"] or "",
        "response_data": products.get("data", []),
        "tool_call_count": len(result["past_calls_history"]),
        "is_error": not bool(products.get("data")),
    }


__all__ = [
    "AgenticCatalogTools",
    "CATALOG_TOOLS",
    "CATALOG_TOOLS_DESCRIPTION",
    "CatalogService",
    "CatalogSubAgentState",
    "build_catalog_app",
    "catalog_agent_node",
    "catalog_app",
    "planner_node",
    "tool_executor_node",
]
