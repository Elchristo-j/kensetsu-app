from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.job_list, name='job_list'),

    # ▼ これを追記（お知らせ詳細へのURL）
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),

    # 案件詳細・作成・編集
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/create/', views.create_job, name='create_job'),
    path('job/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    
    # 応募関連
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/cancel/', views.cancel_application, name='cancel_application'),
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    
    # ★契約フロー
    path('adopt/<int:application_id>/', views.adopt_applicant, name='adopt_applicant'),
    path('reject-applicant/<int:application_id>/', views.reject_applicant, name='reject_applicant'),
    path('contract/<int:application_id>/', views.contract_application, name='contract_application'),
    path('complete/<int:application_id>/', views.complete_job_work, name='complete_job_work'),
    path('review/<int:application_id>/', views.submit_review, name='submit_review'),
    
    # チャット・通知
    path('application/<int:application_id>/chat/', views.chat_room, name='chat_room'),
    path('notifications/', views.notifications, name='notifications'),
    
    #コンタクトフォーム
    path('contact/', views.contact, name='contact'),
    
    # プロフィール・マイページ
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('mypage/', views.mypage, name='mypage'), # 追加
    
    path('favorite/add/', views.add_favorite_area, name='add_favorite_area'),
    path('favorite/delete/<int:area_id>/', views.delete_favorite_area, name='delete_favorite_area'),
    
    # 管理・静的ページ
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve/<int:user_id>/', views.approve_profile, name='approve_profile'),
    path('reject/<int:user_id>/', views.reject_profile, name='reject_profile'),
    path('about/', views.about_view, name='about'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('law/', views.law_view, name='law'),
    path('guide/', views.guide_view, name='guide_view'),
    
    # プラン・決済
    path('plan/', views.subscription_plans, name='subscription_plans'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('payment/success/', views.payment_success, name='payment_success'),

    # ... 他のURL ...
    path('blocked-list/', views.blocked_list, name='blocked_list'),
    path('unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),

    path('favorite-search/', views.favorite_search_view, name='favorite_search_view'),

    # ▼ jobs/urls.py の urlpatterns の中に追加
    path('ura-profiles/', views.ura_profile_list, name='ura_profile_list'),

    # ▼ これを追記（裏プロフィール編集ページへのURL）
    path('ura-profile/edit/', views.edit_ura_profile, name='edit_ura_profile'),

    # ▼ これを追記（カレンダー編集ページへのURL）
    path('ura-profile/calendar/', views.edit_availability, name='edit_availability'),

    # ▼ jobs/urls.py の urlpatterns の中に追加
    path('ura-profiles/', views.ura_profile_list, name='ura_profile_list'),
    path('ura-profile/<int:pk>/', views.ura_profile_detail, name='ura_profile_detail'), # ←これを追加！
    ]