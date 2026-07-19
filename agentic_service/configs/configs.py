"""Common runtime configuration values."""

from __future__ import annotations

import os


LOG_LEVEL = os.getenv("ECOM_AGENT_LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv(
    "ECOM_AGENT_LOG_FORMAT",
    "%(asctime)s | %(levelname)-8s | %(message)s",
)

ECOM_TOOLS_API_URL = os.getenv("ECOM_TOOLS_API_URL", "http://127.0.0.1:8000")
HTTP_REQUEST_TIMEOUT = float(os.getenv("ECOM_HTTP_REQUEST_TIMEOUT", "5"))
MAX_AGENT_ITERATIONS = int(os.getenv("ECOM_MAX_AGENT_ITERATIONS", "15"))

USERS_PAGE_LIMIT = int(os.getenv("ECOM_USERS_PAGE_LIMIT", "10"))
USERS_PAGE_OFFSET = int(os.getenv("ECOM_USERS_PAGE_OFFSET", "0"))
