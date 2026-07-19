"""Streamlit panel for the ecommerce agent."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)


class StreamlitLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.logs: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        formatted = self.format(record)
        self.logs.append(formatted)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configs.configs import (  # noqa: E402
    ECOM_TOOLS_API_URL,
    HTTP_REQUEST_TIMEOUT,
    USERS_PAGE_LIMIT,
    USERS_PAGE_OFFSET,
)
from ecom_agent import ecom_agent  # noqa: E402


st.set_page_config(
    page_title="Ecommerce Agent Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _tools_api_url() -> str:
    return (ECOM_TOOLS_API_URL or "http://127.0.0.1:8000").rstrip("/")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_customers(
    search: str,
    name: str,
    customer_id: str,
    email: str,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    params = {
        "search": search or None,
        "name": name or None,
        "customer_id": customer_id or None,
        "email": email or None,
        "limit": limit,
        "offset": offset,
    }
    response = requests.get(
        f"{_tools_api_url()}/users/ids",
        params=params,
        headers={"accept": "application/json"},
        timeout=HTTP_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def invoke_agent(user_query: str, user_id: str) -> tuple[Dict[str, Any], List[str]]:
    handler = StreamlitLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        result = ecom_agent.invoke(
            {
                "user_query": user_query,
                "user_id": user_id,
                "request_type": "unknown",
                "tool_call_count": 0,
                "agent_response": "",
                "response_data": [],
                "is_error": False,
            }
        )
    finally:
        root_logger.removeHandler(handler)

    return result, handler.logs


def user_label(user: Dict[str, Any]) -> str:
    name = user.get("name") or "Unnamed customer"
    user_id = user.get("user_id") or "unknown"
    email = user.get("email") or "no email"
    return f"{user_id} | {name} | {email}"


def render_metric_row(result: Dict[str, Any]) -> None:
    data = result.get("response_data") or []
    cols = st.columns(4)
    cols[0].metric("Route", str(result.get("request_type", "unknown")).title())
    cols[1].metric("Tool Calls", result.get("tool_call_count", 0))
    cols[2].metric("Results", len(data))
    cols[3].metric("Status", "Error" if result.get("is_error") else "OK")


def flatten_order_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for order in items:
        products = order.get("items") or []
        product_names = [
            item.get("product", {}).get("product_name", "")
            for item in products
            if item.get("product")
        ]

        rows.append(
            {
                "order_id": order.get("order_id"),
                "date": order.get("order_date"),
                "status": order.get("order_status"),
                "amount": order.get("total_amount"),
                "items": ", ".join(product_names[:3]),
                "product_count": order.get("total_items_processed"),
                "products": ", ".join(product_names[:3]),
            }
        )
    return rows


def render_results(result: Dict[str, Any], logs: List[str] | None = None) -> None:
    response_data = result.get("response_data") or []

    st.subheader("Agent Response")
    if result.get("is_error"):
        st.warning(result.get("agent_response") or "The agent could not complete the request.")
    else:
        st.success(result.get("agent_response") or "Request completed.")

    render_metric_row(result)

    st.subheader("Results")
    if not response_data:
        st.info("No structured results returned.")
    else:
        route = result.get("request_type")
        if route == "order":
            st.dataframe(flatten_order_rows(response_data), width='stretch', hide_index=True)
        else:
            st.dataframe(response_data, width='stretch', hide_index=True)

    with st.expander("Raw agent payload"):
        st.json(result)

    if logs:
        with st.expander("Agent logs"):
            st.code("\n".join(logs), language="text")


def render_customer_results(result: Dict[str, Any], logs: List[str] | None = None) -> None:
    response_data = result.get("response_data") or []

    st.subheader("Agent Response")
    if result.get("is_error"):
        st.warning(result.get("agent_response") or "The agent could not complete the request.")
    else:
        st.success(result.get("agent_response") or "Request completed.")

    if not response_data:
        st.info("No structured results returned.")
    else:
        st.subheader("Records")
        st.dataframe(response_data, width='stretch', hide_index=True)

    if logs:
        with st.expander("Agent logs"):
            st.code("\n".join(logs), language="text")


def render_customer_details(selected_user: Dict[str, Any] | None) -> None:
    if not selected_user:
        st.info("No customer selected yet.")
        return

    st.subheader("Customer Details")
    detail_cols = st.columns(3)
    detail_cols[0].write(f"**User ID**\n{selected_user.get('user_id', '-')}")
    detail_cols[1].write(f"**Name**\n{selected_user.get('name', '-')}")
    detail_cols[2].write(f"**Email**\n{selected_user.get('email', '-')}")


def get_selected_customer() -> Dict[str, Any] | None:
    stored_user = st.session_state.get("selected_user")
    if stored_user:
        return stored_user

    try:
        users_payload = fetch_customers(
            search="",
            name="",
            customer_id="",
            email="",
            limit=5,
            offset=0,
        )
        users = users_payload.get("data", [])
        if users:
            return users[0]
    except Exception:
        return None

    return None


def render_dev_mode() -> Dict[str, Any] | None:
    with st.sidebar:
        st.subheader("Customer Lookup")
        search = st.text_input("Search", placeholder="Angel, U000610, email")
        name = st.text_input("Name", placeholder="Angel")
        customer_id = st.text_input("Customer ID", placeholder="U000610")
        email = st.text_input("Email", placeholder="donaldgarcia@example.net")

        lookup_cols = st.columns(2)
        limit = lookup_cols[0].number_input(
            "Limit",
            min_value=1,
            max_value=100,
            value=USERS_PAGE_LIMIT,
            step=1,
        )
        offset = lookup_cols[1].number_input(
            "Offset",
            min_value=0,
            value=USERS_PAGE_OFFSET,
            step=1,
        )

        if st.button("Refresh customers", width='stretch'):
            fetch_customers.clear()

        try:
            users_payload = fetch_customers(
                search=search.strip(),
                name=name.strip(),
                customer_id=customer_id.strip(),
                email=email.strip(),
                limit=int(limit),
                offset=int(offset),
            )
            users = users_payload.get("data", [])
            total = users_payload.get("total", len(users))
        except Exception as exc:
            users = []
            total = 0
            st.error(f"Could not load customers from {_tools_api_url()}: {exc}")

        st.caption(f"{len(users)} shown / {total} matched")
        selected_user = st.selectbox(
            "Selected Identity",
            users,
            format_func=user_label,
            disabled=not users,
        )

        if selected_user:
            st.session_state["selected_user"] = selected_user
            st.divider()
            st.text_input("User ID", value=selected_user.get("user_id", ""), disabled=True)
            st.text_input("Name", value=selected_user.get("name", ""), disabled=True)
            st.text_input("Email", value=selected_user.get("email", ""), disabled=True)

    query_examples = [
        "Show me my latest completed orders",
        "Find clothing products between 150 and 300",
        "Show me the cheapest product in Sports",
    ]

    with st.container(border=True):
        st.subheader("Query")
        query = st.text_area(
            "Customer request",
            value=st.session_state.get("query", query_examples[0]),
            height=110,
            placeholder="Show me my latest completed orders",
            label_visibility="collapsed",
            key="query",
        )

        action_cols = st.columns([1, 1, 3])
        run_clicked = action_cols[0].button("Run Agent", type="primary", width='stretch')
        clear_clicked = action_cols[1].button("Clear", width='stretch')

        example = action_cols[2].selectbox(
            "Examples",
            [""] + query_examples,
            label_visibility="collapsed",
        )
        if example:
            st.session_state["query"] = example
            st.rerun()

    if clear_clicked:
        st.session_state.pop("last_result", None)
        st.session_state.pop("last_agent_logs", None)
        st.session_state["query"] = ""
        st.rerun()

    if run_clicked:
        if not selected_user:
            st.error("Select a customer identity first.")
        elif not query.strip():
            st.error("Enter a query before running the agent.")
        else:
            with st.spinner("Agent is working..."):
                try:
                    result, logs = invoke_agent(
                        user_query=query.strip(),
                        user_id=selected_user["user_id"],
                    )
                    st.session_state["last_result"] = result
                    st.session_state["last_agent_logs"] = logs
                except Exception as exc:
                    st.session_state["last_result"] = {
                        "request_type": "unknown",
                        "tool_call_count": 0,
                        "agent_response": f"Agent execution failed: {exc}",
                        "response_data": [],
                        "is_error": True,
                    }
                    st.session_state["last_agent_logs"] = []

    if "last_result" in st.session_state:
        with st.container(border=True):
            render_results(
                st.session_state["last_result"],
                logs=st.session_state.get("last_agent_logs"),
            )

    render_customer_details(selected_user)

    st.text_area(
        "Customer request",
        value=st.session_state.get("customer_query", ""),
        height=110,
        placeholder="Show me my latest completed orders",
        key="customer_query",
    )

    running = st.session_state.get("customer_query_running", False)
    button_label = "Stop Query" if running else "Start Query"
    if st.button(button_label, type="primary"):
        if running:
            st.session_state["customer_query_running"] = False
            st.session_state.pop("last_customer_result", None)
        elif not st.session_state.get("customer_query", "").strip():
            st.error("Enter a query before starting the agent.")
        elif not selected_user:
            st.error("Select a customer before running the agent.")
        else:
            st.session_state["customer_query_running"] = True
            with st.spinner("Agent is working..."):
                try:
                    result, logs = invoke_agent(
                        user_query=st.session_state["customer_query"].strip(),
                        user_id=selected_user["user_id"],
                    )
                    st.session_state["last_customer_result"] = result
                    st.session_state["last_agent_logs"] = logs
                except Exception as exc:
                    st.session_state["last_customer_result"] = {
                        "request_type": "unknown",
                        "tool_call_count": 0,
                        "agent_response": f"Agent execution failed: {exc}",
                        "response_data": [],
                        "is_error": True,
                    }
                    st.session_state["last_agent_logs"] = []
                finally:
                    st.session_state["customer_query_running"] = False

    if "last_customer_result" in st.session_state:
        with st.container(border=True):
            render_customer_results(
                st.session_state["last_customer_result"],
                logs=st.session_state.get("last_agent_logs"),
            )

    return selected_user


def render_customer_mode() -> Dict[str, Any] | None:
    selected_user = get_selected_customer()
    if selected_user:
        st.session_state["selected_user"] = selected_user

    render_customer_details(selected_user)

    st.text_area(
        "Customer request",
        value=st.session_state.get("customer_query", ""),
        height=110,
        placeholder="Show me my latest completed orders",
        key="customer_query",
    )

    running = st.session_state.get("customer_query_running", False)
    button_label = "Stop Query" if running else "Start Query"
    if st.button(button_label, type="primary"):
        if running:
            st.session_state["customer_query_running"] = False
            st.session_state.pop("last_customer_result", None)
            st.session_state.pop("last_agent_logs", None)
        elif not st.session_state.get("customer_query", "").strip():
            st.error("Enter a query before starting the agent.")
        elif not selected_user:
            st.error("Select a customer before running the agent.")
        else:
            st.session_state["customer_query_running"] = True
            with st.spinner("Agent is working..."):
                try:
                    result, logs = invoke_agent(
                        user_query=st.session_state["customer_query"].strip(),
                        user_id=selected_user["user_id"],
                    )
                    st.session_state["last_customer_result"] = result
                    st.session_state["last_agent_logs"] = logs
                except Exception as exc:
                    st.session_state["last_customer_result"] = {
                        "request_type": "unknown",
                        "tool_call_count": 0,
                        "agent_response": f"Agent execution failed: {exc}",
                        "response_data": [],
                        "is_error": True,
                    }
                    st.session_state["last_agent_logs"] = []
                finally:
                    st.session_state["customer_query_running"] = False

    if "last_customer_result" in st.session_state:
        with st.container(border=True):
            render_customer_results(
                st.session_state["last_customer_result"],
                logs=st.session_state.get("last_agent_logs"),
            )

    return selected_user


def main() -> None:
    st.title("Ecommerce Agent")
    customer_mode = st.toggle(
        "Customer Mode",
        value=st.session_state.get("customer_mode", False),
        key="customer_mode",
    )

    if customer_mode:
        render_customer_mode()
    else:
        render_dev_mode()


if __name__ == "__main__":
    main()
