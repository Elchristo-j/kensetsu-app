from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('lp/client/', views.LpClientView.as_view(), name='lp_client'),
    path('lp/worker/', views.LpWorkerView.as_view(), name='lp_worker'),
    path('column/worker-shortage-2030/', views.ArticleWorkerShortageView.as_view(), name='article_worker_shortage'),
    path('column/reduce-outsourcing-cost/', views.ArticleReduceCostView.as_view(), name='article_reduce_cost'),
]