## アプリ概要
### アプリ名
-  働ログ
### 内容
- 管理者・社員が使いやすいタイムカードアプリ
## 開発環境構築手順

1. **仮想環境の作成・有効化**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **必要なパッケージのインストール**
    ```bash
    pip install -r requirements.txt
    ```

3. **マイグレーションファイルの作成**
    ```bash
    python manage.py makemigrations
    ```

4. **データベースのマイグレーション実行**
    ```bash
    python manage.py migrate
    ```

5. **管理ユーザーの作成**
    ```bash
    python manage.py createsuperuser
    ```

6. **開発サーバーの起動**
    ```bash
    python manage.py runserver
    ```

## accountsアプリの初期設定
### 我々で以下を実施することで、ユーザーはサービスが利用可能になる。
- 企業の登録
- 当該企業の管理者ユーザーの登録
### superuser権限を持ったユーザーでログイン後、admin画面から行ってください。

## Gitの運用ルール
## レビュー方法
