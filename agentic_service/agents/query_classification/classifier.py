"""Query classification module for routing ecommerce requests."""

from __future__ import annotations

import logging

from typing import Any, Dict, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from langsmith import traceable

from agents.common import AgentState, build_chat_ollama
from configs.agents import (
    ALLOWED_REQUEST_TYPES,
    CLASSIFICATION_PROMPT,
    CLASSIFIER_MODEL,
)

logger = logging.getLogger(__name__)

class IntentClassificationResponse(BaseModel):
    request_type: Literal["catalog", "order", "unknown"]
    is_invalid: bool


def build_intent_chain():
    llm = build_chat_ollama(CLASSIFIER_MODEL)
    intent_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CLASSIFICATION_PROMPT),
            ("human", "{user_query}"),
        ]
    )
    return intent_prompt | llm.with_structured_output(IntentClassificationResponse)


@traceable
def categorize_query(state: Dict[str, Any]) -> Dict[str, Any]:
    chain = build_intent_chain()
    result: IntentClassificationResponse = chain.invoke(
        {"user_query": state["user_query"]}
    )

    request_type = result.request_type
    if request_type not in ALLOWED_REQUEST_TYPES:
        request_type = "unknown"

    return {
        "request_type": request_type,
        "is_valid_request": not result.is_invalid,
    }

@traceable
def router_node(state: AgentState) -> AgentState:
    result = categorize_query(state)

    logger.info("User Query: %s", state["user_query"])
    logger.info("request_type: %s", result["request_type"])

    return {
        **state,
        "request_type": result["request_type"],
        "is_error": not result["is_valid_request"],
    }
