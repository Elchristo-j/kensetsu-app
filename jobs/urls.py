# jobs/urls.py (順番を入れ替えた完全版)

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('create/', views.create_job, name='create_job'),
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/cancel/', views.cancel_application, name='cancel_application'),
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    path('application/<int:application_id>/adopt/', views.adopt_applicant, name='adopt_applicant'),
    path('application/<int:application_id>/chat/', views.chat_room, name='chat_room'),

    # ★ここが重要：editを詳細(int)より上に置く！
    path('profile/edit/', views.profile_edit, name='profile_edit'), 
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
]