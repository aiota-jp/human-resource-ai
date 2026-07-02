"""ログイン認証サービス"""
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db


def ensure_default_admin() -> None:
    """初回起動用の管理者を作成する。ID: admin / PW: password"""
    conn = get_db()
    exists = conn.execute("SELECT id FROM user WHERE username = ?", ("admin",)).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("password"), "admin"),
        )
        conn.commit()
    conn.close()


def authenticate(username: str, password: str) -> dict | None:
    conn = get_db()
    user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return dict(user)
    return None


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("ログインしてください", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper
