from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('create/', views.create_job, name='create_job'),
    path('job/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('job/<int:job_id>/cancel/', views.cancel_application, name='cancel_application'),
    path('job/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    path('application/<int:application_id>/adopt/', views.adopt_applicant, name='adopt_applicant'),
    path('application/<int:application_id>/chat/', views.chat_room, name='chat_room'),
    path('notifications/', views.notifications, name='notifications'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('accounts/profile/edit/', views.profile_edit, name='profile_edit'),
    
    # ★追加：お気に入りエリアの追加と削除の道（URL）
    path('favorite-area/add/', views.add_favorite_area, name='add_favorite_area'),
    path('favorite-area/<int:area_id>/delete/', views.delete_favorite_area, name='delete_favorite_area'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('law/', views.law_view, name='law'),
    path('about/', views.about_view, name='about'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('law/', views.law_view, name='law'),

    # ... 既存のパス ...
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('law/', views.law_view, name='law'),
    # jobs/views.py の一番下に追加

    def about_view(request):
        return render(request, 'jobs/about.html')

    def terms_view(request):
        return render(request, 'jobs/terms.html')

    def privacy_view(request):
        return render(request, 'jobs/privacy.html')

    def law_view(request):
        return render(request, 'jobs/law.html')
]