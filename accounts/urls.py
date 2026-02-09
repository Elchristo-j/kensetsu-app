from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- 認証・プロフィール基本 ---
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),

    # --- マイページ・プランアップグレード ---
    path('mypage/', views.mypage, name='mypage'),
    path('upgrade/', views.upgrade_plan_page, name='upgrade_plan_page'),
    
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
]