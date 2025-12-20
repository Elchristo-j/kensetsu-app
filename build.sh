#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# ↓ここが新しい「最強の1行」です（管理者作成）
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin12345') if not User.objects.filter(username='admin').exists() else print('Admin already exists')" | python manage.py shell