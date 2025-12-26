from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # トップページ
    path('', views.home, name='home'),

    # 詳細ページ
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),

    # 仕事作成
    path('create/', views.create_job, name='create_job'),
    
    # ★追加：仕事削除
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),

    # 応募ボタン
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    
    # ★追加：応募キャンセル
    path('job/<int:job_id>/cancel/', views.cancel_application, name='cancel_application'),

    # 応募者リストページ
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),

    # チャットルーム
    path('application/<int:application_id>/chat/', views.chat_room, name='chat_room'),

    # 採用機能
    path('application/<int:application_id>/adopt/', views.adopt_applicant, name='adopt_applicant'),

    # ログイン機能
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)