from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import User

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get("/ids")
def get_unique_user_ids(
    search: str | None = Query(
        default=None,
        description="Search by customer name, customer id, or email"
    ),
    name: str | None = Query(default=None),
    customer_id: str | None = Query(default=None),
    email: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    base_query = (
        db.query(User.user_id, User.name, User.email, User.signup_date)
        .filter(User.user_id.isnot(None))
    )

    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.filter(
            or_(
                User.name.ilike(search_pattern),
                User.user_id.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    if name:
        base_query = base_query.filter(User.name.ilike(f"%{name}%"))

    if customer_id:
        base_query = base_query.filter(User.user_id.ilike(f"%{customer_id}%"))

    if email:
        base_query = base_query.filter(User.email.ilike(f"%{email}%"))

    total = base_query.count()

    users = (
        base_query
        .order_by(User.user_id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [user._asdict() for user in users]
    }
