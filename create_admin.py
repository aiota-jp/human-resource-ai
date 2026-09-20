# create_admin.py

from werkzeug.security import generate_password_hash

from database import get_db, init_db


# 動作確認用の初期ユーザー
DEFAULT_USERS = (
    ("admin", "password", "admin"),
    ("staff", "password", "staff"),
    ("user", "password", "user"),
)


def create_users():
    """データベースを初期化し、動作確認用ユーザーを作成する"""

    # テーブルとサンプルデータを作成
    init_db()

    conn = get_db()

    for username, password, role in DEFAULT_USERS:

        # ユーザーがすでに存在するか確認
        existing_user = conn.execute(
            "SELECT id FROM user WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            print(f"{username} ユーザーはすでに登録されています。")
            continue

        # パスワードをハッシュ化
        hashed_password = generate_password_hash(password)

        # ユーザーを登録
        conn.execute(
            """
            INSERT INTO user (username, password, role)
            VALUES (?, ?, ?)
            """,
            (username, hashed_password, role)
        )

        print(f"{username} ユーザーを作成しました。")

    conn.commit()
    conn.close()

    print()
    print("初期ユーザーの作成が完了しました。")
    print("--------------------------------")
    print("管理者 : admin / password")
    print("担当者 : staff / password")
    print("一般   : user / password")
    print("--------------------------------")


if __name__ == "__main__":
    create_users()