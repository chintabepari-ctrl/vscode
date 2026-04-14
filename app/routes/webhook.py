from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EmailMessage
from app.schemas import EmailWebhookPayload, WebhookResponse
from app.utils import parse_email_header_date

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/email", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def receive_email(
    payload: EmailWebhookPayload,
    db: Session = Depends(get_db),
) -> WebhookResponse:
    subject = payload.headers.subject or ""
    email_date_raw = payload.headers.date
    email_date = parse_email_header_date(email_date_raw)

    email = EmailMessage(
        from_email=str(payload.from_email),
        to_email=str(payload.to_email),
        subject=subject,
        email_date=email_date,
        email_date_raw=email_date_raw,
        size=payload.size,
        raw_email=payload.raw_email,
        headers_json=payload.headers.model_dump(by_alias=True),
        is_read=False,
    )
    db.add(email)
    db.commit()
    db.refresh(email)

    return WebhookResponse(status="stored", id=email.id)
