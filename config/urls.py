from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# 不要になった User, HttpResponse のインポートは削除しました

# 貴方様のプロジェクト構成に合わせて、jobsアプリのviewsを読み込みます
from jobs import views

# --- 緊急用コード（関数）はすべて削除しました ---

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 緊急用のURLも削除しました ---

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