from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('lp/client/', views.LpClientView.as_view(), name='lp_client'),
    path('lp/worker/', views.LpWorkerView.as_view(), name='lp_worker'),
]