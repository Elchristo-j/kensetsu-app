from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from jobs import views as job_views  # 運営用のviewを呼び出すために追加
from accounts import views as account_views # ★追加1：accountsのviewsを読み込む

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # jobsアプリの機能
    path('', include('jobs.urls')),
    
    # サインアップ、ログイン関連
    path('accounts/', include('accounts.urls')),

    # --- 運営専用機能 ---
    path('operator/dashboard/', job_views.admin_dashboard, name='admin_dashboard'),
    path('operator/approve/<int:user_id>/', job_views.approve_profile, name='approve_profile'),
    path('operator/reject/<int:user_id>/', job_views.reject_profile, name='reject_profile'),

    path('profile/', account_views.mypage, name='mypage'), # ★追加2：マイページへの通路
]

# 画像表示設定
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)