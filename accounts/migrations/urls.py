from accounts import views as account_views # ← これを追加

urlpatterns = [
    # ... 他のURL ...
    path('profile/', account_views.my_profile, name='my_profile'), # ← これを追加
]