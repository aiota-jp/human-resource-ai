# AI人事・研修業務支援システム

## 起動方法

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

ブラウザで `http://localhost:5000` を開きます。

## 初期ログイン

- ユーザーID: `admin`
- パスワード: `password`

## 追加済み機能

- 社員CRUD
- 研修登録・研修履歴入力
- 評価一覧・AIコメント生成
- Excel取込・Excel出力
- 日報登録・一覧
- 社内文書検索
- FAQチャット
- 認証・ログイン必須デコレータ
- CSS / JavaScript

Difyを使う場合は `.env` に `DIFY_API_KEY` を設定してください。未設定の場合はローカル確認用のダミー回答で動作します。
