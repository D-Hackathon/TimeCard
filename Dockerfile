FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ← ここに pkg-config と MySQL 開発ヘッダを追加
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# 依存関係（リポ直下の requirements.txt を参照）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir uwsgi

# 静的/メディア
COPY . /code

RUN mkdir -p /static /media
