from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # jobsアプリの機能
    path('', include('jobs.urls')),
    
    # サインアップ、ログイン関連
    path('accounts/', include('accounts.urls')),
]

# 画像（プロフィール写真など）を表示するための設定
# 本番環境（Render）でも画像が扱えるように if DEBUG を外した状態で追加します
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)