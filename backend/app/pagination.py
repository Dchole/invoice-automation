"""Shared pagination helper for list endpoints."""
from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Query


def paginate(query: Query, page: int = 1, per_page: int = 25) -> dict[str, Any]:
    """Apply pagination to a SQLAlchemy query and return paginated result."""
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # Cap at 100

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
