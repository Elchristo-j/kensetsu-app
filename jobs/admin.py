from django.contrib import admin
from .models import Job, Application  # 作ったモデルを読み込む

# 管理画面に登録する
admin.site.register(Job)
admin.site.register(Application)