from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User
from django.http import HttpResponse

# 貴方様のプロジェクト構成に合わせて、jobsアプリのviewsを読み込みます
from jobs import views

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

    # トップページ
    path('', views.home, name='home'),

    # 詳細ページ
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),

    # 仕事作成
    path('create/', views.create_job, name='create_job'),

    # 応募ボタン
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),

    # 応募者リストページ
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),

    # ログイン機能
    path('accounts/', include('accounts.urls')),
]

# 画像表示のための設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)