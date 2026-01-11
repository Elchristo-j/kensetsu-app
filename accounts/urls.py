from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # ★追加：マイページ
    path('mypage/', views.mypage, name='mypage'),
    path('upgrade/', views.upgrade_plan_page, name='upgrade_plan_page'), # これを追加
    path('upgrade/<str:plan_type>/', views.create_checkout_session, name='create_checkout_session'),
]