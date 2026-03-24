from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional
from datetime import datetime
import re


# ─────────────────────────────────────────
# 🔐 Auth Models
# ─────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    role: Literal["admin", "user"]


class APIMessage(BaseModel):
    message: str


# ─────────────────────────────────────────
# 👤 User Models
# ─────────────────────────────────────────

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["admin", "user"] = "user"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class ChangePasswordRequest(BaseModel):
    target_username: str = Field(..., min_length=3, max_length=64)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


# ─────────────────────────────────────────
# 🐛 Vulnerability Models
# ─────────────────────────────────────────

SeverityType = Literal["critical", "high", "medium", "low", "info"]
StatusType   = Literal["open", "in_progress", "resolved", "closed", "wont_fix"]


class Vulnerability(BaseModel):
    id: int = Field(..., gt=0)
    title: str = Field(..., min_length=3, max_length=200)
    severity: SeverityType
    status: StatusType = "open"
    description: str = Field(..., min_length=5, max_length=2000)
    assigned_to: Optional[str] = Field(None, max_length=64)
    template: str = Field(..., min_length=1, max_length=100)
    application: str = Field(..., min_length=1, max_length=100)
    module: Optional[str] = Field(None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        # Strip HTML/script tags
        cleaned = re.sub(r"<[^>]+>", "", v).strip()
        if not cleaned:
            raise ValueError("Title cannot be empty after sanitization")
        return cleaned

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        cleaned = re.sub(r"<script[^>]*>.*?</script>", "", v, flags=re.IGNORECASE | re.DOTALL)
        return cleaned.strip()


class UpdateVulnerabilityRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    severity: Optional[SeverityType] = None
    status: Optional[StatusType] = None
    description: Optional[str] = Field(None, min_length=5, max_length=2000)
    assigned_to: Optional[str] = Field(None, max_length=64)
    module: Optional[str] = Field(None, max_length=100)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────
# 📊 Dashboard Models
# ─────────────────────────────────────────

class DashboardFilter(BaseModel):
    template: Optional[str] = Field(None, max_length=100)
    application: Optional[str] = Field(None, max_length=100)
    severity: Optional[SeverityType] = None
    status: Optional[StatusType] = None
    module: Optional[str] = Field(None, max_length=100)
    assigned_to: Optional[str] = Field(None, max_length=64)


class VulnSummaryItem(BaseModel):
    id: int
    title: str
    severity: SeverityType
    status: StatusType
    template: str
    application: str
    module: Optional[str]
    assigned_to: Optional[str]
    created_at: Optional[str]


class DashboardResponse(BaseModel):
    total_vulnerabilities: int
    open_count: int
    resolved_count: int
    critical_count: int
    by_severity: dict[str, int]
    by_application: dict[str, int]
    by_template: dict[str, int]
    by_module: dict[str, int]
    by_status: dict[str, int]
    recent: list[VulnSummaryItem]


# ─────────────────────────────────────────
# 🔔 Notification Models
# ─────────────────────────────────────────

class NotificationEvent(BaseModel):
    id: int = Field(..., gt=0)
    vuln_id: int
    vuln_title: str
    event_type: Literal["created", "status_changed", "severity_changed", "assigned", "resolved"]
    triggered_by: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False


class NotificationResponse(BaseModel):
    notifications: list[NotificationEvent]
    unread_count: int