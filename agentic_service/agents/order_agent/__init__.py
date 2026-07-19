"""Order agent package with tools, service client, and LangGraph workflow."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from langsmith import traceable

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
from agents.order_agent.service import OrderService
from agents.order_agent.tools import AgenticOrderTools
from configs.agents import ORDER_AGENT_MODEL, ORDER_PLANNER_SYSTEM_PROMPT


class OrderSubAgentState(TypedDict):
    user_query: str
    user_id: str
    past_calls_history: List[Dict[str, Any]]
    tool_call: Optional[ToolCall]
    agent_response: Optional[str]
    orders: Dict[str, Any]
    orders_found: bool
    iterations_count: int


agentic_order_service = AgenticOrderTools()
ORDER_TOOLS = {
    "search_orders": agentic_order_service.search_orders,
}
ORDER_TOOLS_DESCRIPTION = build_tools_description(ORDER_TOOLS)

parser = PydanticOutputParser(pydantic_object=AgentDecision)
format_instructions = parser.get_format_instructions()

order_planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            ORDER_PLANNER_SYSTEM_PROMPT,
        ),
        (
            "user",
            """
Customer ID:
{customer_id}

User Query:
{user_query}

Past History:
{history}
""",
        ),
    ]
)

@traceable
def order_planner_node(state: OrderSubAgentState) -> OrderSubAgentState:
    logger.info("=" * 80)
    logger.info("ORDER PLANNER NODE")
    logger.info("=" * 80)

    if state["user_id"] is None:
        raise ValueError("Order Agent needs user_id")

    history = json.dumps(state["past_calls_history"], indent=2, ensure_ascii=False)
    prompt = order_planner_prompt.format(
        user_query=state["user_query"],
        customer_id=state["user_id"],
        history=history,
        tools_desc=ORDER_TOOLS_DESCRIPTION,
        format_instructions=format_instructions,
    )

    llm = build_chat_ollama(ORDER_AGENT_MODEL)
    response = llm.with_structured_output(AgentDecision).invoke(prompt)

    logger.info("Planner Response: %s", response)

    return {
        **state,
        "agent_response": response.agent_response,
        "tool_call": response.tool_call,
        "iterations_count": state["iterations_count"] + 1,
        "orders": state["orders"],
    }


@traceable
def order_tool_executor_node(state: OrderSubAgentState) -> OrderSubAgentState:
    logger.info("=" * 80)
    logger.info("ORDER TOOL EXECUTOR")
    logger.info("=" * 80)

    tool_call = state["tool_call"]

    if tool_call is None:
        orders = state.get("orders", empty_tool_result())
        return {
            **state,
            "orders_found": bool(orders.get("data")),
        }

    tool_name = tool_call.name
    args = tool_call.args or {}
    args["customer_id"] = state["user_id"]
    tool_fn = ORDER_TOOLS.get(tool_name)

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
        "orders": tool_result,
        "tool_call": None,
    }


def build_order_app():
    graph = StateGraph(OrderSubAgentState)
    graph.add_node("planner", order_planner_node)
    graph.add_node("tool", order_tool_executor_node)
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


order_app = build_order_app()


def order_agent_node(state: AgentState) -> AgentState:
    result = order_app.invoke(
        {
            "user_query": state["user_query"],
            "user_id": state["user_id"],
            "past_calls_history": [],
            "tool_call": None,
            "agent_response": None,
            "orders": empty_tool_result(),
            "orders_found": False,
            "iterations_count": 0,
        }
    )

    orders = result.get("orders") or empty_tool_result()

    return {
        **state,
        "agent_response": result["agent_response"] or "",
        "response_data": orders.get("data", []),
        "tool_call_count": len(result["past_calls_history"]),
        "is_error": not bool(orders.get("data")),
    }


__all__ = [
    "AgenticOrderTools",
    "ORDER_TOOLS",
    "ORDER_TOOLS_DESCRIPTION",
    "OrderService",
    "OrderSubAgentState",
    "build_order_app",
    "order_agent_node",
    "order_app",
    "order_planner_node",
    "order_tool_executor_node",
]
