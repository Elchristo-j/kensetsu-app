from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User
from django.http import HttpResponse

# --- ここから：緊急用管理者作成コード ---
def create_emergency_admin(request):
    # ユーザー名 'admin' がいない場合のみ作成
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'AdminPass123!')
        return HttpResponse("<h1>成功！</h1><p>新しいDBに管理者を作成しました。<br>ユーザー名: admin<br>パスワード: AdminPass123!</p>")
    else:
        return HttpResponse("<h1>確認</h1><p>管理者は既に存在しています。<br>パスワード: AdminPass123! で試してみてください。</p>")
# --- ここまで ---

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 緊急用のURL
    path('emergency-create/', create_emergency_admin),

    # トップページなど
    path('', include('jobs.urls')), 
    path('accounts/', include('accounts.urls')),
]

# 画像表示の設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    