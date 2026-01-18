#!/usr/bin/env bash
# エラーが起きたら即終了させる
set -o errexit

# 1. pipを最新にする（念のため）
pip install --upgrade pip

# 2. 指示書（requirements.txt）に従ってインストール
pip install -r requirements.txt

# 3. 静的ファイルをまとめる
python manage.py collectstatic --no-input

# 4. データベースの更新
python manage.py migrate