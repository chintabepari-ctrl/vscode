from math import ceil

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EmailMessage
from app.schemas import DetailContext, InboxQueryParams, PaginationContext
from app.utils import build_query_string, format_datetime, format_size

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


def _build_base_query(params: InboxQueryParams):
    query = select(EmailMessage)

    if params.q:
        pattern = f"%{params.q.lower()}%"
        query = query.where(
            or_(
                func.lower(EmailMessage.from_email).like(pattern),
                func.lower(EmailMessage.to_email).like(pattern),
                func.lower(EmailMessage.subject).like(pattern),
            )
        )

    if params.status == "read":
        query = query.where(EmailMessage.is_read.is_(True))
    elif params.status == "unread":
        query = query.where(EmailMessage.is_read.is_(False))

    return query


def _get_unread_count(db: Session) -> int:
    stmt = select(func.count()).select_from(EmailMessage).where(EmailMessage.is_read.is_(False))
    return db.scalar(stmt) or 0


@router.get("/")
def inbox(
    request: Request,
    q: str = Query(default=""),
    status_filter: str = Query(default="all", alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    params = InboxQueryParams(q=q, status=status_filter, page=page, per_page=per_page)
    base_query = _build_base_query(params)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_items = db.scalar(count_stmt) or 0
    total_pages = max(ceil(total_items / params.per_page), 1)
    current_page = min(params.page, total_pages)
    offset = (current_page - 1) * params.per_page

    stmt = (
        base_query.order_by(EmailMessage.created_at.desc(), EmailMessage.id.desc())
        .offset(offset)
        .limit(params.per_page)
    )
    emails = db.scalars(stmt).all()

    pagination = PaginationContext(
        page=current_page,
        per_page=params.per_page,
        total_items=total_items,
        total_pages=total_pages,
        has_previous=current_page > 1,
        has_next=current_page < total_pages,
    )

    query_state = {
        "q": params.q,
        "status": params.status,
        "per_page": params.per_page,
    }

    return templates.TemplateResponse(
        request,
        "inbox.html",
        {
            "emails": emails,
            "pagination": pagination,
            "query_state": query_state,
            "unread_count": _get_unread_count(db),
            "build_query_string": build_query_string,
            "format_size": format_size,
            "format_datetime": format_datetime,
        },
    )


@router.get("/emails/{email_id}")
def email_detail(
    request: Request,
    email_id: int,
    return_to: str = Query(default="/"),
    db: Session = Depends(get_db),
):
    email = db.get(EmailMessage, email_id)
    if email is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    if not email.is_read:
        email.is_read = True
        db.commit()
        db.refresh(email)

    detail = DetailContext(
        id=email.id,
        from_email=email.from_email,
        to_email=email.to_email,
        subject=email.subject,
        email_date=format_datetime(email.email_date),
        email_date_raw=email.email_date_raw,
        size_display=format_size(email.size),
        size_bytes=email.size,
        raw_email=email.raw_email,
        headers_json=email.headers_json or {},
        is_read=email.is_read,
        created_at=format_datetime(email.created_at) or "",
    )

    return templates.TemplateResponse(
        request,
        "email_detail.html",
        {
            "email": detail,
            "return_to": return_to or "/",
            "unread_count": _get_unread_count(db),
        },
    )


@router.post("/emails/{email_id}/toggle-read")
def toggle_read(
    email_id: int,
    next_url: str = Form(default="/"),
    db: Session = Depends(get_db),
):
    email = db.get(EmailMessage, email_id)
    if email is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    email.is_read = not email.is_read
    db.commit()
    return RedirectResponse(url=next_url or "/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/emails/{email_id}/delete")
def delete_email(
    email_id: int,
    next_url: str = Form(default="/"),
    db: Session = Depends(get_db),
):
    email = db.get(EmailMessage, email_id)
    if email is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    db.delete(email)
    db.commit()
    return RedirectResponse(url=next_url or "/", status_code=status.HTTP_303_SEE_OTHER)
