from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # ★ここに追加：案件一覧（検索結果）ページ
    path('search/', views.job_list, name='job_list'),

    # 案件詳細・作成・編集
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/create/', views.create_job, name='create_job'),
    path('job/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    
    # 応募・採用関連
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/cancel/', views.cancel_application, name='cancel_application'),
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    
    # ※お客様の環境に合わせて関数名（adopt_applicantなど）を維持しています
    path('adopt/<int:application_id>/', views.adopt_applicant, name='adopt_applicant'),
    path('reject-applicant/<int:application_id>/', views.reject_applicant, name='reject_applicant'),
    
    # チャット・通知
    path('application/<int:application_id>/chat/', views.chat_room, name='chat_room'),
    path('notifications/', views.notifications, name='notifications'),
    
    # プロフィール・お気に入り
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('favorite/add/', views.add_favorite_area, name='add_favorite_area'),
    path('favorite/delete/<int:area_id>/', views.delete_favorite_area, name='delete_favorite_area'),
    
    # 管理・静的ページ
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:user_id>/', views.approve_profile, name='approve_profile'),
    path('reject/<int:user_id>/', views.reject_profile, name='reject_profile'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('law/', views.law_view, name='law'),
    
    # Q&A・ガイドページ
    path('guide/', views.guide_view, name='guide_view'),
    
    # プラン・決済関連
    path('plan/', views.subscription_plans, name='subscription_plans'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('payment/success/', views.payment_success, name='payment_success'),
]