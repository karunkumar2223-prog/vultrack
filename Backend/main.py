from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from collections import Counter
from datetime import datetime
from typing import Optional
import pandas as pd
import os

from Backend.models import (
    LoginRequest, TokenResponse, APIMessage,
    CreateUserRequest, ChangePasswordRequest,
    Vulnerability, UpdateVulnerabilityRequest,
    DashboardFilter, DashboardResponse, VulnSummaryItem,
    NotificationEvent, NotificationResponse,
    SeverityType, StatusType,
)
from Backend.auth import decode_token, create_token, verify_password, hash_password
from Backend.utils import read_csv, write_csv, USERS, ADMIN, VULN, NOTIFICATIONS

app = FastAPI(title="VulnTrack API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# ──────────────────────────────────────────
# 🔐 Auth Helpers
# ──────────────────────────────────────────

def get_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def admin_required(user: dict = Depends(get_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ──────────────────────────────────────────
# 🔑 Login
# ──────────────────────────────────────────

@app.post("/login", response_model=TokenResponse)
def login(req: LoginRequest) -> TokenResponse:
    users = read_csv(USERS)
    admins = read_csv(ADMIN)
    df = pd.concat([users, admins], ignore_index=True)

    match = df[df["username"] == req.username]
    if match.empty:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    row = match.iloc[0]
    if not verify_password(req.password, str(row["password"])):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"username": row["username"], "role": row["role"]})
    return TokenResponse(access_token=token, role=row["role"])


# ──────────────────────────────────────────
# 👤 User Management (Admin Only)
# ──────────────────────────────────────────

@app.post("/admin/create-user", response_model=APIMessage)
def create_user(req: CreateUserRequest, _: dict = Depends(admin_required)) -> APIMessage:
    users = read_csv(USERS)
    if req.username in users["username"].values:
        raise HTTPException(status_code=400, detail="User already exists")

    new_row = pd.DataFrame([{
        "username": req.username,
        "password": hash_password(req.password),
        "role": req.role,
    }])
    write_csv(pd.concat([users, new_row], ignore_index=True), USERS)
    return APIMessage(message="User created successfully")


@app.post("/admin/change-password", response_model=APIMessage)
def change_password(req: ChangePasswordRequest, _: dict = Depends(admin_required)) -> APIMessage:
    for filepath in [USERS, ADMIN]:
        df = read_csv(filepath)
        mask = df["username"] == req.target_username
        if mask.any():
            df.loc[mask, "password"] = hash_password(req.new_password)
            write_csv(df, filepath)
            return APIMessage(message="Password updated")
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/admin/promote/{username}", response_model=APIMessage)
def promote_user(username: str, _: dict = Depends(admin_required)) -> APIMessage:
    users = read_csv(USERS)
    mask = users["username"] == username
    if not mask.any():
        raise HTTPException(status_code=404, detail="User not found")
    users.loc[mask, "role"] = "admin"
    write_csv(users, USERS)
    return APIMessage(message=f"{username} promoted to admin")


@app.delete("/admin/delete-user/{username}", response_model=APIMessage)
def delete_user(username: str, _: dict = Depends(admin_required)) -> APIMessage:
    users = read_csv(USERS)
    if username not in users["username"].values:
        raise HTTPException(status_code=404, detail="User not found")
    write_csv(users[users["username"] != username], USERS)
    return APIMessage(message="User deleted")


# ──────────────────────────────────────────
# 🐛 Vulnerabilities
# ──────────────────────────────────────────

@app.get("/vulnerabilities")
def list_vulns(user: dict = Depends(get_user)) -> list[dict]:
    df = read_csv(VULN)
    if user["role"] == "user":
        df = df[df["assigned_to"] == user["username"]]
    return df.to_dict(orient="records")


@app.post("/vulnerabilities", response_model=APIMessage)
def add_vuln(vuln: Vulnerability, _: dict = Depends(admin_required)) -> APIMessage:
    df = read_csv(VULN)
    if str(vuln.id) in df["id"].astype(str).values:
        raise HTTPException(status_code=400, detail="Vulnerability ID already exists")

    row = vuln.model_dump()
    row["created_at"] = datetime.utcnow().isoformat()
    row["updated_at"] = None
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write_csv(df, VULN)

    _create_notification(
        vuln_id=vuln.id,
        vuln_title=vuln.title,
        event_type="created",
        triggered_by=_["username"] if isinstance(_, dict) else "admin",
        message=f"New vulnerability '{vuln.title}' added ({vuln.severity.upper()})",
    )
    return APIMessage(message="Vulnerability added")


@app.patch("/vulnerabilities/{vuln_id}", response_model=APIMessage)
def update_vuln(
    vuln_id: int,
    req: UpdateVulnerabilityRequest,
    user: dict = Depends(admin_required),
) -> APIMessage:
    df = read_csv(VULN)
    mask = df["id"].astype(str) == str(vuln_id)
    if not mask.any():
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    updates = req.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.utcnow().isoformat()
    for col, val in updates.items():
        df.loc[mask, col] = val

    write_csv(df, VULN)

    event = "status_changed" if "status" in updates else "severity_changed" if "severity" in updates else "assigned"
    _create_notification(
        vuln_id=vuln_id,
        vuln_title=str(df.loc[mask, "title"].iloc[0]),
        event_type=event,
        triggered_by=user["username"],
        message=f"Vulnerability #{vuln_id} updated by {user['username']}",
    )
    return APIMessage(message="Vulnerability updated")


# ──────────────────────────────────────────
# 📊 Admin Dashboard
# ──────────────────────────────────────────

@app.post("/admin/dashboard", response_model=DashboardResponse)
def dashboard(filters: DashboardFilter, _: dict = Depends(admin_required)) -> DashboardResponse:
    df = read_csv(VULN)

    if filters.template:
        df = df[df["template"] == filters.template]
    if filters.application:
        df = df[df["application"] == filters.application]
    if filters.severity:
        df = df[df["severity"] == filters.severity]
    if filters.status:
        df = df[df["status"] == filters.status]
    if filters.module:
        df = df[df["module"] == filters.module]
    if filters.assigned_to:
        df = df[df["assigned_to"] == filters.assigned_to]

    recent_rows = df.tail(5).to_dict(orient="records")
    recent = [VulnSummaryItem(**{k: v for k, v in r.items() if k in VulnSummaryItem.model_fields}) for r in recent_rows]

    return DashboardResponse(
        total_vulnerabilities=len(df),
        open_count=int((df["status"] == "open").sum()),
        resolved_count=int((df["status"] == "resolved").sum()),
        critical_count=int((df["severity"] == "critical").sum()),
        by_severity=dict(Counter(df["severity"].dropna())),
        by_application=dict(Counter(df["application"].dropna())),
        by_template=dict(Counter(df["template"].dropna())),
        by_module=dict(Counter(df["module"].dropna())),
        by_status=dict(Counter(df["status"].dropna())),
        recent=recent,
    )


# ──────────────────────────────────────────
# 🔔 Notifications
# ──────────────────────────────────────────

def _create_notification(
    vuln_id: int,
    vuln_title: str,
    event_type: str,
    triggered_by: str,
    message: str,
) -> None:
    df = read_csv(NOTIFICATIONS)
    new_id = int(df["id"].max()) + 1 if not df.empty and "id" in df.columns else 1
    new_row = {
        "id": new_id,
        "vuln_id": vuln_id,
        "vuln_title": vuln_title,
        "event_type": event_type,
        "triggered_by": triggered_by,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
    }
    write_csv(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), NOTIFICATIONS)


@app.get("/admin/notifications", response_model=NotificationResponse)
def get_notifications(
    unread_only: bool = Query(False),
    _: dict = Depends(admin_required),
) -> NotificationResponse:
    df = read_csv(NOTIFICATIONS)
    if unread_only:
        df = df[df["read"] == False]  # noqa: E712

    items = [NotificationEvent(**row) for row in df.to_dict(orient="records")]
    return NotificationResponse(
        notifications=sorted(items, key=lambda x: x.timestamp, reverse=True),
        unread_count=int((df["read"] == False).sum()),  # noqa: E712
    )


@app.post("/admin/notifications/mark-read", response_model=APIMessage)
def mark_notifications_read(_: dict = Depends(admin_required)) -> APIMessage:
    df = read_csv(NOTIFICATIONS)
    df["read"] = True
    write_csv(df, NOTIFICATIONS)
    return APIMessage(message="All notifications marked as read")