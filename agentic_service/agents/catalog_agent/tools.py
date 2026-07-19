"""Tool implementations for the catalog subagent."""

from __future__ import annotations

from typing import Optional

from agents.catalog_agent.service import CatalogService


catalog_service = CatalogService()


class AgenticCatalogTools:
    @staticmethod
    def fetch_categories(limit: int = 50, offset: int = 0):
        """
        Name:
            fetch_categories

        Description:
            Fetch all available product categories from the catalog.

        Parameters:
            limit (int, optional):
                Maximum number of categories to return.
                Default: 50.

            offset (int, optional):
                Number of categories to skip before returning results.
                Default: 0.

        Returns:
            list[str]:
                Category names available in the catalog.
        """
        return catalog_service.fetch_categories(limit=limit, offset=offset)

    @staticmethod
    def validate_category(category: str):
        """
        Name:
            validate_category

        Description:
            Checks whether a category exists in the catalog.

        Parameters:
            category (str):
                Category name to validate. Use a category explicitly provided
                by the user or returned from fetch_categories.

        Returns:
            dict:
                {
                    "valid": bool,
                    "available_categories": list[str]
                }
        """
        categories = catalog_service.fetch_categories()

        return {
            "valid": category.lower() in [c.lower() for c in categories],
            "available_categories": categories,
        }

    @staticmethod
    def search_products(
        product_name: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ):
        """
        Name:
            search_products

        Description:
            Search products in the ecommerce catalog using one or more filters.

        Parameters:
            product_name (str, optional):
                Product name or partial product name explicitly mentioned by
                the user.

            category (str, optional):
                Product category. Use only a category explicitly mentioned by
                the user after validating it, or a category returned by
                fetch_categories. Do not invent category values.

            brand (str, optional):
                Product brand explicitly mentioned by the user.

            min_price (float, optional):
                Minimum product price. Use only when the user gives a lower
                price bound.

            max_price (float, optional):
                Maximum product price. Use only when the user gives an upper
                price bound.

            min_rating (float, optional):
                Minimum product rating. Use only when the user explicitly asks
                for products rated at least a certain value.

            max_rating (float, optional):
                Maximum product rating. Use only when the user explicitly asks
                for products rated at most a certain value.

            sort_by (str, optional):
                Sort order. Supported values are:
                - product_name:asc
                - product_name:desc
                - category:asc
                - category:desc
                - brand:asc
                - brand:desc
                - price:asc
                - price:desc
                - rating:asc
                - rating:desc

            limit (int, optional):
                Maximum number of products to return.
                Default: 10.

            offset (int, optional):
                Number of products to skip before returning results.
                Default: 0.

        Rules:
            - Only pass parameters known from the user query.
            - Never invent filters.
            - Unknown filters should be None.
            - Category must be validated or obtained from fetch_categories.

        Returns:
            dict:
                Search response with total, limit, offset, and data fields.
        """
        return catalog_service.search_products(
            product_name=product_name,
            category=category,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            max_rating=max_rating,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )
