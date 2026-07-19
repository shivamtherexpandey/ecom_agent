"""HTTP service client for order tools."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from configs.configs import ECOM_TOOLS_API_URL, HTTP_REQUEST_TIMEOUT


class OrderService:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or ECOM_TOOLS_API_URL).rstrip("/")
        self.order_api = f"{self.base_url}/orders/customer"

    def search_orders(
        self,
        customer_id: str,
        order_status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_total_items: Optional[int] = None,
        max_total_items: Optional[int] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Dict[str, Any]:
        params = {
            "order_status": order_status,
            "start_date": start_date,
            "end_date": end_date,
            "min_total_items": min_total_items,
            "max_total_items": max_total_items,
            "min_amount": min_amount,
            "max_amount": max_amount,
            "sort_by": [sort_by] if isinstance(sort_by, str) else sort_by,
            "limit": limit,
            "offset": offset,
        }

        response = requests.get(
            f"{self.order_api}/{customer_id}",
            params=params,
            timeout=HTTP_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        return response.json()
