"""HTTP service client for catalog tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from configs.configs import ECOM_TOOLS_API_URL, HTTP_REQUEST_TIMEOUT


class CatalogService:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or ECOM_TOOLS_API_URL).rstrip("/")
        self.category_api = f"{self.base_url}/products/categories"
        self.product_api = f"{self.base_url}/products/search"
        self._category_cache: Optional[List[str]] = None

    def fetch_categories(self, limit: int = 50, offset: int = 0) -> List[str]:
        response = requests.get(
            self.category_api,
            params={"limit": limit, "offset": offset},
            timeout=HTTP_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        payload = response.json()
        categories = payload.get("categories") or payload.get("data") or []

        self._category_cache = categories
        return categories

    def is_valid_category(self, category: Optional[str]) -> bool:
        if not category:
            return False

        categories = self._category_cache or self.fetch_categories()
        return category.lower() in [item.lower() for item in categories]

    def search_products(
        self,
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
    ) -> Dict[str, Any]:
        params = {
            "product_name": product_name,
            "category": category,
            "brand": brand,
            "min_price": min_price,
            "max_price": max_price,
            "min_rating": min_rating,
            "max_rating": max_rating,
            "sort_by": [sort_by] if isinstance(sort_by, str) else sort_by,
            "limit": limit,
            "offset": offset,
        }

        response = requests.get(
            self.product_api,
            params=params,
            timeout=HTTP_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        return response.json()
