"""Final ecommerce agent workflow integration."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents.catalog_agent import catalog_agent_node
from agents.common import AgentState
from agents.order_agent import order_agent_node
from agents.query_classification import router_node
from configs.agents import UNKNOWN_REQUEST_RESPONSE
from langsmith import traceable

@traceable
def route_request(state: AgentState):
    if state["request_type"] == "catalog":
        return "catalog"

    if state["request_type"] == "order":
        return "order"

    return "unknown"


@traceable
def unknown_node(state: AgentState):
    return {
        **state,
        "is_error": True,
        "agent_response": UNKNOWN_REQUEST_RESPONSE,
        "response_data": [],
    }


def build_ecom_agent():
    ecom_graph = StateGraph(AgentState)
    ecom_graph.add_node("router", router_node)
    ecom_graph.add_node("catalog", catalog_agent_node)
    ecom_graph.add_node("order", order_agent_node)
    ecom_graph.add_node("unknown", unknown_node)
    ecom_graph.set_entry_point("router")
    ecom_graph.add_conditional_edges(
        "router",
        route_request,
        {
            "catalog": "catalog",
            "order": "order",
            "unknown": "unknown",
        },
    )
    ecom_graph.add_edge("catalog", END)
    ecom_graph.add_edge("order", END)
    ecom_graph.add_edge("unknown", END)
    return ecom_graph.compile()


ecom_agent = build_ecom_agent()

__all__ = [
    "AgentState",
    "build_ecom_agent",
    "ecom_agent",
    "route_request",
    "unknown_node",
]
