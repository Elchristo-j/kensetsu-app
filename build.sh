#!/usr/bin/env bash
# エラーが起きたら即終了させる設定
set -o errexit

# 1. Poetryを使ってライブラリをインストール
poetry install

# 2. 静的ファイルの集約（CSSや画像をまとめる）
poetry run python manage.py collectstatic --no-input

# 3. データベースの更新
poetry run python manage.py migrate