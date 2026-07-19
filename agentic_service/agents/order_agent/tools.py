"""Tool implementations for the order subagent."""

from __future__ import annotations

from typing import Optional

from agents.order_agent.service import OrderService


order_service = OrderService()


class AgenticOrderTools:
    @staticmethod
    def search_orders(
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
    ):
        """
        Name:
            search_orders

        Description:
            Search customer orders using one or more filters.

        Parameters:
            customer_id (str):
                Unique customer identifier. This is mandatory and must come
                from the selected user identity/context, not from the user's
                free-text query.

            order_status (str, optional):
                Order status explicitly mentioned by the user. Do not invent
                status values. The API performs text matching for this field.

            start_date (str, optional):
                Inclusive start date for order_date filtering.
                Format: YYYY-MM-DD.

            end_date (str, optional):
                Inclusive end date for order_date filtering.
                Format: YYYY-MM-DD.

            min_total_items (int, optional):
                Minimum number of items in an order. Use only when the user
                gives a lower item-count bound.

            max_total_items (int, optional):
                Maximum number of items in an order. Use only when the user
                gives an upper item-count bound.

            min_amount (float, optional):
                Minimum order amount. Use only when the user gives a lower
                amount bound.

            max_amount (float, optional):
                Maximum order amount. Use only when the user gives an upper
                amount bound.

            sort_by (str, optional):
                Sort order. Supported values are:
                - order_date:asc
                - order_date:desc
                - amount:asc
                - amount:desc

            limit (int, optional):
                Maximum number of orders to return.
                Default: 10.

            offset (int, optional):
                Number of orders to skip before returning results.
                Default: 0.

        Rules:
            - Only pass filters explicitly mentioned by the user.
            - Never invent values.
            - Unknown values must remain None.
            - customer_id is mandatory.

        Returns:
            dict:
                Search response with total, limit, offset, and data fields.
        """
        return order_service.search_orders(
            customer_id=customer_id,
            order_status=order_status,
            start_date=start_date,
            end_date=end_date,
            min_total_items=min_total_items,
            max_total_items=max_total_items,
            min_amount=min_amount,
            max_amount=max_amount,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )
