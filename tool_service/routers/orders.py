from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc

from database import get_db
from models import Order, OrderItem, Product
from schemas import OrdersSearchResponse

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

SORTABLE_FIELDS = {
    "order_date": Order.order_date,
    "amount": Order.total_amount,
}


def apply_sorting(query, sort_by: list[str] | None):
    if not sort_by:
        return query.order_by(Order.order_date.desc())

    order_by_fields = []

    for sort_item in sort_by:
        field_name, _, direction = sort_item.partition(":")
        column = SORTABLE_FIELDS.get(field_name)

        if not column:
            continue

        if direction.lower() == "asc":
            order_by_fields.append(asc(column))
        else:
            order_by_fields.append(desc(column))

    if not order_by_fields:
        return query.order_by(Order.order_date.desc())

    return query.order_by(*order_by_fields)


@router.get("/customer/{customer_id}", response_model=OrdersSearchResponse)
def get_customer_orders(
    customer_id: str,

    order_status: str | None = Query(default=None),

    start_date: str | None = Query(
        default=None,
        description="Example: 2025-01-01"
    ),
    end_date: str | None = Query(
        default=None,
        description="Example: 2025-12-31"
    ),

    min_total_items: int | None = Query(default=None, ge=0),
    max_total_items: int | None = Query(default=None, ge=0),

    min_amount: float | None = Query(default=None, ge=0),
    max_amount: float | None = Query(default=None, ge=0),

    sort_by: list[str] | None = Query(
        default=None,
        description="Example: sort_by=order_date:desc&sort_by=amount:asc"
    ),

    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),

    db: Session = Depends(get_db)
):
    base_query = (
        db.query(
            Order.order_id,
            Order.user_id,
            Order.order_date,
            Order.order_status,
            Order.total_amount,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_items_processed")
        )
        .outerjoin(OrderItem, Order.order_id == OrderItem.order_id)
        .filter(Order.user_id == customer_id)
        .group_by(Order.order_id)
    )

    if order_status:
        base_query = base_query.filter(
            Order.order_status.ilike(f"%{order_status}%")
        )

    if start_date:
        base_query = base_query.filter(Order.order_date >= start_date)

    if end_date:
        base_query = base_query.filter(Order.order_date <= end_date)

    if min_amount is not None:
        base_query = base_query.filter(Order.total_amount >= min_amount)

    if max_amount is not None:
        base_query = base_query.filter(Order.total_amount <= max_amount)

    if min_total_items is not None:
        base_query = base_query.having(
            func.coalesce(func.sum(OrderItem.quantity), 0) >= min_total_items
        )

    if max_total_items is not None:
        base_query = base_query.having(
            func.coalesce(func.sum(OrderItem.quantity), 0) <= max_total_items
        )

    total = base_query.count()

    orders = (
        apply_sorting(base_query, sort_by)
        .offset(offset)
        .limit(limit)
        .all()
    )

    order_ids = [order.order_id for order in orders]

    items = (
        db.query(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.product_id)
        .filter(OrderItem.order_id.in_(order_ids))
        .all()
    )

    order_items_map = {}

    for item, product in items:
        order_items_map.setdefault(item.order_id, []).append({
            "order_item_id": item.order_item_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "item_price": item.item_price,
            "item_total": item.item_total,
            "product": {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category,
                "brand": product.brand,
                "price": product.price,
                "rating": product.rating,
            }
        })

    response_data = []

    for order in orders:
        response_data.append({
            "order_id": order.order_id,
            "user_id": order.user_id,
            "order_date": order.order_date,
            "order_status": order.order_status,
            "total_amount": order.total_amount,
            "total_items_processed": order.total_items_processed,
            "items": order_items_map.get(order.order_id, [])
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": response_data
    }