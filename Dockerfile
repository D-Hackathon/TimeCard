FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

<<<<<<< HEAD
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates \
=======
# ← ここに pkg-config と MySQL 開発ヘッダを追加
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev curl ca-certificates \
>>>>>>> 7a96186 (fix Dockerfile)
 && rm -rf /var/lib/apt/lists/*

WORKDIR /code

<<<<<<< HEAD
# 依存関係（リポ直下の requirements.txt を参照）
=======
>>>>>>> 7a96186 (fix Dockerfile)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir uwsgi

<<<<<<< HEAD
# プロジェクト一式
COPY . /code

# 静的/メディア
=======
COPY . /code

>>>>>>> 7a96186 (fix Dockerfile)
RUN mkdir -p /static /media
