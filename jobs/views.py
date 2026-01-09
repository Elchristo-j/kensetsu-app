from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test  # ここにまとめました
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail 
from django.conf import settings
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea
from .forms import JobForm, MessageForm, ProfileForm

# --- 通知作成の補助関数 ---
def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

# --- 運営者判定の補助関数（関数の外に出しました） ---
def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# --- お仕事関連 ---

def home(request):
    """トップページ：募集中の仕事を検索・一覧表示"""
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query', '')
    area_filter = request.GET.get('area_filter', '')

    if area_filter == 'favorites' and request.user.is_authenticated:
        fav_areas = FavoriteArea.objects.filter(user=request.user)
        if fav_areas.exists():
            q_objects = Q()
            for area in fav_areas:
                if area.city:
                    q_objects |= Q(prefecture=area.prefecture, city__icontains=area.city)
                else:
                    q_objects |= Q(prefecture=area.prefecture)
            jobs = jobs.filter(q_objects)
        else:
            jobs = jobs.none()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(prefecture__icontains=query) |
            Q(city__icontains=query)
        ).distinct()
        
    return render(request, 'jobs/home.html', {
        'jobs': jobs, 
        'query': query, 
        'area_filter': area_filter
    })

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    is_applied = False
    if request.user.is_authenticated:
        is_applied = Application.objects.filter(job=job, applicant=request.user).exists()
    return render(request, 'jobs/job_detail.html', {'job': job, 'is_applied': is_applied})

@login_required
def create_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            return redirect('home')
    else:
        form = JobForm()
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': False})

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        return redirect('job_detail', job_id=job.id)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': True})

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user:
        job.delete()
    return redirect('home')

@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        pref = request.POST.get('prefecture')
        city = request.POST.get('city', '').strip()
        if pref:
            FavoriteArea.objects.get_or_create(user=request.user, prefecture=pref, city=city)
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    area = get_object_or_404(FavoriteArea, id=area_id, user=request.user)
    area.delete()
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        application, created = Application.objects.get_or_create(job=job, applicant=request.user)
        if created:
            create_notification(job.created_by, f"「{job.title}」に新しい応募がありました。", f"/job/{job.id}/applicants/")
        return redirect('chat_room', application_id=application.id)
    return redirect('job_detail', job_id=job.id)

@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    application = get_object_or_404(Application, job=job, applicant=request.user)
    if application.status == 'accepted':
        job.headcount += 1
        job.is_closed = False
        job.save()
    application.delete()
    return redirect('job_detail', job_id=job.id)

@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        return redirect('home')
    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

@login_required
def adopt_applicant(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    if request.user == job.created_by and application.status != 'accepted':
        application.status = 'accepted'
        application.save()
        create_notification(application.applicant, f"「{job.title}」に採用されました！", f"/application/{application.id}/chat/")
        if job.headcount > 0:
            job.headcount -= 1
            if job.headcount <= 0:
                job.is_closed = True
            job.save()
    return redirect('job_applicants', job_id=job.id)

@login_required
def chat_room(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    if request.user != application.applicant and request.user != application.job.created_by:
        return redirect('home')
    # --- ここを追加：自分宛てのメッセージを既読にする ---
    from .models import Message  # 関数内でインポートしておけば確実です
    Message.objects.filter(
        application=application, 
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    # ② 【ここを追加！】 このチャットに関する「通知」もまとめて既読にする
    request.user.notifications.filter(link__contains=f'/application/{application.id}/', is_read=False).update(is_read=True)
    # -----------------------------------------------     
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            message.save()
            recipient = application.job.created_by if request.user == application.applicant else application.applicant
            create_notification(recipient, f"{request.user.username}さんからメッセージがあります。", f"/application/{application.id}/chat/")
            return redirect('chat_room', application_id=application_id)
    else:
        form = MessageForm()
    return render(request, 'jobs/chat_room.html', {'application': application, 'form': form})

@login_required
def notifications(request):
    # --- 修正：url を link に変えました ---
    request.user.notifications.filter(is_read=False).exclude(link__contains='chat').update(is_read=True)
    # ------------------------------------
    
    notifications = request.user.notifications.order_by('-created_at') # 新しい順に並べる
    return render(request, 'jobs/notifications.html', {'notifications': notifications})
    user_notifications = request.user.notifications.all().order_by('-created_at')
    user_notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'jobs/notifications.html', {'notifications': user_notifications})

@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    Profile.objects.get_or_create(user=target_user)
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    fav_areas = target_user.favorite_areas.all()
    from accounts.models import PREFECTURES
    return render(request, 'jobs/profile_detail.html', {'target_user': target_user, 'jobs': jobs, 'fav_areas': fav_areas, 'prefectures': PREFECTURES})

@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if 'id_card_image' in request.FILES:
                try:
                    send_mail(
                        subject="【重要】本人確認の申請が届きました",
                        message=f"{request.user.username} さんから身分証画像が届きました。",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.EMAIL_HOST_USER],
                        fail_silently=True,
                    )
                except:
                    pass
            return redirect('profile_detail', user_id=request.user.id)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'jobs/profile_edit.html', {'form': form})

# --- 運営専用ダッシュボード機能 ---

@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """運営専用：本人確認の申請一覧"""
    pending_profiles = Profile.objects.filter(
        id_card_image__isnull=False, 
        is_verified=False
    ).exclude(id_card_image='') 
    
    return render(request, 'jobs/admin_dashboard.html', {
        'pending_profiles': pending_profiles
    })

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    """運営専用：本人確認を承認する"""
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    profile.is_verified = True
    profile.save()

    create_notification(
        recipient=target_user,
        message="🎉 本人確認が承認されました！プロフィールに認証バッジが付与されました。",
        link=f"/profile/{target_user.id}/"
    )
    return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    """運営専用：本人確認を否認（却下）する"""
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    
    # 画像を物理削除
    if profile.id_card_image:
        profile.id_card_image.delete()
    profile.save()

    create_notification(
        recipient=target_user,
        message="⚠️ 本人確認書類に不備がありました。お手数ですが、もう一度正しい画像をアップロードしてください。",
        link="/accounts/profile/edit/"
    )
    return redirect('admin_dashboard')
    def terms_view(request): return render(request, 'jobs/terms.html')
    def privacy_view(request): return render(request, 'jobs/privacy.html')
    def law_view(request): return render(request, 'jobs/law.html')
    def about_view(request): return render(request, 'jobs/about.html')