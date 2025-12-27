from django.urls import path
from . import views

urlpatterns = [
    # トップページ（お仕事一覧）
    path('', views.home, name='home'),
    
    # お仕事詳細
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    
    # お仕事作成・削除
    path('create/', views.create_job, name='create_job'),
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    
    # 応募関連
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/cancel/', views.cancel_application, name='cancel_application'),
    
    # 応募者一覧（投稿者用）
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    
    # 採用決定
    path('application/<int:application_id>/adopt/', views.adopt_applicant, name='adopt_applicant'),
    
    # チャットルーム
    path('application/<int:application_id>/chat/', views.chat_room, name='chat_room'),
    
    # プロフィール（マイページ）
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]