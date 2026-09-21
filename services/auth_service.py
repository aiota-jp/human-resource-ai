"""ログイン認証・ロール認可サービス"""
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db


DEFAULT_USERS = (
    ("admin", "password", "admin"),
    ("staff", "password", "staff"),
    ("user", "password", "user"),
    ("EMP001", "password", "user"),
)


def ensure_default_users() -> None:
    """動作確認用の初期ユーザーを作成する。既存ユーザーは変更しない。"""
    conn = get_db()
    for username, password, role in DEFAULT_USERS:
        exists = conn.execute(
            "SELECT id FROM user WHERE username = ?", (username,)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )
    conn.commit()
    conn.close()


def ensure_default_admin() -> None:
    """後方互換用。初期ユーザー3種類を作成する。"""
    ensure_default_users()


def authenticate(username: str, password: str) -> dict | None:
    conn = get_db()
    user = conn.execute(
        """
        SELECT u.*, e.id AS employee_id, e.name AS employee_name
          FROM user u
          LEFT JOIN employee e
                 ON e.employee_no = u.username AND e.is_active = 1
         WHERE u.username = ?
        """,
        (username,),
    ).fetchone()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return dict(user)
    return None


def login_required(view_func):
    """ログイン済みユーザーだけアクセスを許可する。"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("ログインしてください", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles):
    """指定したロールだけアクセスを許可する。"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("ログインしてください", "warning")
                return redirect(url_for("login"))

            if session.get("role") not in allowed_roles:
                flash("この機能を利用する権限がありません", "danger")
                return redirect(url_for("index"))

            return view_func(*args, **kwargs)
        return wrapper
    return decorator
