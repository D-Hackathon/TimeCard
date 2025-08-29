# app/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# 必要に応じてビルド依存パッケージを調整
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential libpq-dev curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
  && pip install --no-cache-dir uwsgi

# アプリ本体
COPY app/ ./

# 静的/メディア出力先（共有ボリューム）
RUN mkdir -p /static /media

# CMD は compose 側で uwsgi を起動
