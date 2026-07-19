from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from database import get_db
from models import Product
from schemas import ProductSearchResponse

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

SORTABLE_FIELDS = {
    "product_name": Product.product_name,
    "category": Product.category,
    "brand": Product.brand,
    "price": Product.price,
    "rating": Product.rating,
}

@router.get("/categories")
def get_unique_categories(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    base_query = (
        db.query(Product.category)
        .filter(Product.category.isnot(None))
        .distinct()
    )

    total = base_query.count()

    categories = (
        base_query
        .order_by(Product.category.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [category[0] for category in categories]
    }


def apply_sorting(query, sort_by: list[str] | None):
    if not sort_by:
        return query.order_by(Product.product_id.asc())

    order_by_fields = []

    for sort_item in sort_by:
        field_name, _, direction = sort_item.partition(":")

        column = SORTABLE_FIELDS.get(field_name)

        if not column:
            continue

        if direction.lower() == "desc":
            order_by_fields.append(desc(column))
        else:
            order_by_fields.append(asc(column))

    if not order_by_fields:
        return query.order_by(Product.product_id.asc())

    return query.order_by(*order_by_fields)


@router.get("/search", response_model=ProductSearchResponse)
def search_products(
    product_name: str | None = Query(default=None),
    category: str | None = Query(default=None),
    brand: str | None = Query(default=None),

    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),

    min_rating: float | None = Query(default=None),
    max_rating: float | None = Query(default=None),

    sort_by: list[str] | None = Query(
        default=None,
        description="Example: sort_by=price:asc&sort_by=rating:desc"
    ),

    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),

    db: Session = Depends(get_db)
):
    query = db.query(Product)

    if product_name:
        query = query.filter(Product.product_name.ilike(f"%{product_name}%"))

    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)

    if max_rating is not None:
        query = query.filter(Product.rating <= max_rating)

    total = query.count()

    query = apply_sorting(query, sort_by)

    products = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": products
    }