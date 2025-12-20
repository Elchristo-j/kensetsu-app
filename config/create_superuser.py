import os
import django

# Djangoの設定を読み込む
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

# すでにadminがいるか確認して、いなければ作る
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
    print("★管理ユーザー(admin)を作成しました！")
else:
    print("★管理ユーザーはすでに存在します。")