"""Agentic ecommerce assistant service package."""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

from ecom_agent import ecom_agent

__all__ = ["ecom_agent"]

# Testing

# result = ecom_agent.invoke({
#     "user_query": "Show me my latest completed orders",
#     "user_id": "U000610",
# })

# print(result)

if __name__ == "__main__":
    png = ecom_agent.get_graph().draw_mermaid_png()

    with open("graph.png", "wb") as f:
        f.write(png)