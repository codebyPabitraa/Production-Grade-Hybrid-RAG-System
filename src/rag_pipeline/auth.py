from __future__ import annotations

import base64
import hmac
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, asdict
from typing import Any

from rag_pipeline.storage import auth_root


AUTH_ROOT = auth_root()
USERS_FILE = AUTH_ROOT / "users.json"
OTPS_FILE = AUTH_ROOT / "otps.json"
HISTORY_FILE = AUTH_ROOT / "question_history.json"
TOKEN_SECRET = os.getenv("RAG_JWT_SECRET", "dev-secret-change-me")
TOKEN_TTL_SECONDS = 60 * 60 * 8


@dataclass(slots=True)
class UserRecord:
    username: str
    email: str
    password_hash: str
    role: str = "user"
    verified: bool = False


def ensure_auth_store() -> None:
    AUTH_ROOT.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]", encoding="utf-8")
    if not OTPS_FILE.exists():
        OTPS_FILE.write_text("[]", encoding="utf-8")
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


def _read_json(path: Path) -> list[dict[str, Any]]:
    ensure_auth_store()
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def _write_json(path: Path, data: list[dict[str, Any]]) -> None:
    ensure_auth_store()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_question_history(limit: int = 20, user_key: str | None = None) -> list[dict[str, Any]]:
    entries = _read_json(HISTORY_FILE)
    if user_key:
        entries = [entry for entry in entries if entry.get("user_key") == user_key]
    return entries[-limit:][::-1]


def delete_question_history(*, user_key: str, report_path: str) -> bool:
    entries = _read_json(HISTORY_FILE)
    filtered = [entry for entry in entries if not (entry.get("user_key") == user_key and entry.get("report_path") == report_path)]
    if len(filtered) == len(entries):
        return False
    _write_json(HISTORY_FILE, filtered)
    return True


def save_question_history(
    *,
    user_key: str,
    username: str,
    email: str,
    question: str,
    answer: str,
    report_path: str,
    context_precision: float,
    answer_relevancy: float,
    faithfulness: float,
    context_recall: float,
) -> dict[str, Any]:
    entries = _read_json(HISTORY_FILE)
    entry = {
        "user_key": user_key,
        "username": username,
        "email": email,
        "question": question,
        "answer": answer,
        "report_path": report_path,
        "context_precision": context_precision,
        "answer_relevancy": answer_relevancy,
        "faithfulness": faithfulness,
        "context_recall": context_recall,
        "created_utc": int(time.time()),
    }
    entries.append(entry)
    _write_json(HISTORY_FILE, entries)
    return entry


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return base64.urlsafe_b64encode(salt).decode("ascii") + "$" + base64.urlsafe_b64encode(digest).decode("ascii")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_b64, digest_b64 = password_hash.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def register_user(username: str, email: str, password: str, role: str = "user") -> UserRecord:
    users = _read_json(USERS_FILE)
    if any(user.get("username") == username or user.get("email") == email for user in users):
        raise ValueError("User already exists")
    record = UserRecord(
        username=username,
        email=email,
        password_hash=_hash_password(password),
        role=role,
        verified=False,
    )
    users.append(asdict(record))
    _write_json(USERS_FILE, users)
    return record


def generate_otp(email: str) -> str:
    otp = f"{secrets.randbelow(1_000_000):06d}"
    otp_entries = [entry for entry in _read_json(OTPS_FILE) if entry.get("email") != email]
    otp_entries.append(
        {
            "email": email,
            "otp": otp,
            "created_utc": int(time.time()),
        }
    )
    _write_json(OTPS_FILE, otp_entries)
    return otp


def verify_otp(email: str, otp: str) -> bool:
    otp_entries = _read_json(OTPS_FILE)
    now = int(time.time())
    matched = None
    for entry in otp_entries:
        if entry.get("email") == email and entry.get("otp") == otp and now - int(entry.get("created_utc", 0)) <= 900:
            matched = entry
            break
    if matched is None:
        return False
    otp_entries = [entry for entry in otp_entries if entry is not matched]
    _write_json(OTPS_FILE, otp_entries)
    users = _read_json(USERS_FILE)
    for user in users:
        if user.get("email") == email:
            user["verified"] = True
    _write_json(USERS_FILE, users)
    return True


def authenticate_user(username_or_email: str, password: str) -> dict[str, Any] | None:
    users = _read_json(USERS_FILE)
    for user in users:
        if user.get("username") == username_or_email or user.get("email") == username_or_email:
            if user.get("verified") and _verify_password(password, user.get("password_hash", "")):
                return user
    return None


def create_token(user: dict[str, Any]) -> str:
    payload = {
        "sub": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(TOKEN_SECRET.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    token = body + "." + base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return token


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        body, sig = token.split(".", 1)
        expected = hmac.new(TOKEN_SECRET.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
        provided = base64.urlsafe_b64decode(sig + "==")
        if not hmac.compare_digest(expected, provided):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "==").decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def bootstrap_admin_from_env() -> dict[str, Any] | None:
    username = os.getenv("ADMIN_USERNAME", "").strip()
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not username or not email or not password:
        return None
    ensure_auth_store()
    users = _read_json(USERS_FILE)
    password_hash = _hash_password(password)
    for user in users:
        if user.get("email") == email or user.get("username") == username:
            user["role"] = "admin"
            user["username"] = username
            user["email"] = email
            user["password_hash"] = password_hash
            user["verified"] = True
            _write_json(USERS_FILE, users)
            return user
    record = register_user(username, email, password, role="admin")
    users = _read_json(USERS_FILE)
    for user in users:
        if user.get("email") == email:
            user["username"] = username
            user["password_hash"] = password_hash
            user["role"] = "admin"
            user["verified"] = True
    _write_json(USERS_FILE, users)
    return asdict(record)


def reset_admin_password_from_env() -> dict[str, Any] | None:
    username = os.getenv("ADMIN_USERNAME", "").strip()
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not username or not email or not password:
        return None
    ensure_auth_store()
    users = _read_json(USERS_FILE)
    password_hash = _hash_password(password)
    found = False
    for user in users:
        if user.get("email") == email or user.get("username") == username:
            user["username"] = username
            user["email"] = email
            user["password_hash"] = password_hash
            user["role"] = "admin"
            user["verified"] = True
            found = True
    if not found:
        users.append(
            {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "role": "admin",
                "verified": True,
            }
        )
    _write_json(USERS_FILE, users)
    return next((user for user in users if user.get("email") == email or user.get("username") == username), None)
