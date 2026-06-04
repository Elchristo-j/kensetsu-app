from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- 認証・プロフィール基本 ---
    path('signup/', views.signup, name='signup'),
    # メール認証用URL
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),

    # --- AI自己紹介文生成 ---
    path('generate-bio/', views.generate_bio, name='generate_bio'),

    # --- マイページ・プランアップグレード ---
    path('mypage/', views.mypage, name='mypage'),
    path('upgrade/', views.upgrade_plan_page, name='upgrade_plan_page'),

    # 無料ランクアップ（Stripeを通さず GOLD を初月無料付与・1人1回）
    path('free-rankup/', views.free_rankup, name='free_rankup'),
    
    # 決済セッション作成（1つに整理しました）
    path('create-checkout-session/<str:plan_type>/', views.create_checkout_session, name='create_checkout_session'),

    # --- Stripe Webhook ---
    # 重要：Stripeダッシュボードに登録したURLが「.../accounts/stripe-webhook/」なら以下にします
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),

    # --- ブロック機能　ーーー
    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('report/<int:user_id>/', views.report_user, name='report_user'),

    # ★この1行を追加してください！
    path('account/delete/', views.account_delete, name='account_delete'),

    # accounts/urls.py の urlpatterns の中に追加
    path('guide/cancellation-info/', views.delete_guide_only, name='delete_guide_only'),

    path('verification-guide/', views.verification_guide, name='verification_guide'),

    # パスワードリセット
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]