from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.networks import validate_email


class EmailHeaders(BaseModel):
    subject: str = ""
    date: str | None = None
    message_id: str | None = Field(default=None, alias="message-id")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class EmailWebhookPayload(BaseModel):
    from_email: str
    to_email: str
    size: int = Field(ge=0)
    headers: EmailHeaders
    raw_email: str = Field(min_length=1)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def remap_worker_keys(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        remapped = dict(data)
        if "from" in remapped and "from_email" not in remapped:
            remapped["from_email"] = remapped.pop("from")
        if "to" in remapped and "to_email" not in remapped:
            remapped["to_email"] = remapped.pop("to")
        return remapped

    @field_validator("from_email", "to_email")
    @classmethod
    def validate_email_address(cls, value: str) -> str:
        _, normalized = validate_email(value)
        return normalized

    @field_validator("raw_email")
    @classmethod
    def strip_raw_email(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("raw_email must not be empty")
        return cleaned


class WebhookResponse(BaseModel):
    status: str
    id: int


class InboxQueryParams(BaseModel):
    q: str = ""
    status: str = "all"
    page: int = 1
    per_page: int = 10

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"all", "read", "unread"}
        normalized = value.lower()
        if normalized not in allowed:
            return "all"
        return normalized

    @field_validator("page")
    @classmethod
    def validate_page(cls, value: int) -> int:
        return max(value, 1)

    @field_validator("per_page")
    @classmethod
    def validate_per_page(cls, value: int) -> int:
        return min(max(value, 1), 50)


class EmailTemplateItem(BaseModel):
    id: int
    from_email: str
    to_email: str
    subject: str
    email_date: str | None
    size_bytes: int
    size_display: str
    is_read: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class PaginationContext(BaseModel):
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_previous: bool
    has_next: bool


class DetailContext(BaseModel):
    id: int
    from_email: str
    to_email: str
    subject: str
    email_date: str | None
    email_date_raw: str | None
    size_display: str
    size_bytes: int
    raw_email: str
    headers_json: dict[str, Any]
    is_read: bool
    created_at: str
