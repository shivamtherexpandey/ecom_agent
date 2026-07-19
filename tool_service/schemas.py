from pydantic import BaseModel
from typing import Optional


class ProductResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    brand: str
    price: float
    rating: float

    class Config:
        from_attributes = True

class ProductSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ProductResponse]

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    order_date: str
    order_status: str
    total_amount: float

    class Config:
        from_attributes = True


class ProductSearchParams(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

class ProductInfo(BaseModel):
    product_id: str
    product_name: str
    category: str
    brand: str
    price: float
    rating: float | None = None


class OrderItemInfo(BaseModel):
    order_item_id: str
    product_id: str
    quantity: int
    item_price: float
    item_total: float
    product: ProductInfo


class OrderWithItemsResponse(BaseModel):
    order_id: str
    user_id: str
    order_date: str
    order_status: str
    total_amount: float
    total_items_processed: int
    items: list[OrderItemInfo]


class OrdersSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[OrderWithItemsResponse]