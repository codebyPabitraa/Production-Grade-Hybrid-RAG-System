from pathlib import Path

from rag_pipeline.auth import (
    authenticate_user,
    bootstrap_admin_from_env,
    create_token,
    generate_otp,
    register_user,
    reset_admin_password_from_env,
    verify_otp,
    verify_token,
)
from rag_pipeline.app_server import _cookie_value


def test_register_verify_and_login_flow(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    register_user("alice", "alice@example.com", "secret123")
    otp = generate_otp("alice@example.com")
    assert verify_otp("alice@example.com", otp)

    user = authenticate_user("alice", "secret123")
    assert user is not None
    token = create_token(user)
    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"
    assert payload["email"] == "alice@example.com"


def test_admin_bootstrap_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-secret")

    user = bootstrap_admin_from_env()

    assert user is not None
    assert user["role"] == "admin"
    assert user["email"] == "admin@example.com"


def test_reset_admin_password_from_env_updates_existing_user(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "new-secret")

    bootstrap_admin_from_env()
    reset_admin_password_from_env()

    user = authenticate_user("admin", "new-secret")
    assert user is not None
    assert user["role"] == "admin"


def test_cookie_value_extracts_token():
    cookie_header = "foo=1; rag_token=abc123; bar=2"
    assert _cookie_value(cookie_header, "rag_token") == "abc123"
