from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail 
from django.conf import settings
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea
from .forms import JobForm, MessageForm, ProfileForm

def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def home(request):
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
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(prefecture__icontains=query) | Q(city__icontains=query)).distinct()
    return render(request, 'jobs/home.html', {'jobs': jobs, 'query': query, 'area_filter': area_filter})

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

# --- jobs/views.py の該当箇所を上書き ---

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    
    # 自分の投稿には応募できない
    if job.created_by == request.user:
        return redirect('job_detail', job_id=job.id)

    # 1. すでに応募済みかチェック（応募済みの場合はチャットへ）
    application = Application.objects.filter(job=job, applicant=request.user).first()
    if application:
        return redirect('chat_room', application_id=application.id)

    # 2. 【新規応募の場合のみ】ランクごとの応募制限（鉄の掟）をチェック
    profile = request.user.profile
    if not profile.can_apply():
        # 制限に達している場合は、エラーメッセージを出してアップグレード画面へ
        from django.contrib import messages
        messages.error(request, f"今月の応募上限（{profile.monthly_limit}件）に達しました。さらに応募するにはランクアップが必要です。")
        return redirect('upgrade_plan_page')

    # 3. 制限をクリアしていれば応募を作成
    application = Application.objects.create(job=job, applicant=request.user)
    create_notification(job.created_by, f"「{job.title}」に新しい応募がありました。", f"/job/{job.id}/applicants/")
    
    return redirect('chat_room', application_id=application.id)

@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    application = get_object_or_404(Application, job=job, applicant=request.user)

    # --- ここを追加：募集主に「応募が取り消された」ことを知らせる ---
    create_notification(
        recipient=job.created_by,
        message=f"「{job.title}」への {request.user.username} さんの応募が取り消されました。",
        link=f"/job/{job.id}/"
    )
    # -------------------------------------------------------

    if application.status == 'accepted':
        message = f"「{job.title}」について、募集先の都合により誠に勝手ながら採用が取り消されました。恐れ入りますが、他の案件をご検討ください。"
        job.headcount += 1
        job.is_closed = False
        job.save()
    else:
        message = f"「{job.title}」について、募集主の都合により今回は見送りとなりました。"

    create_notification(recipient=application.applicant, message=message, link=f"/job/{job.id}/")
    application.delete()
    return redirect('job_applicants', job_id=job.id)
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
    return redirect('job_applicants', job_id=job.id)

@login_required
def chat_room(request, application_id):
    # get_object_or_404 ではなく、データがない場合に通知一覧へ戻す処理
    application = Application.objects.filter(pk=application_id).first()
    if not application:
        # メッセージとともに通知一覧へ戻す
        return redirect('notifications')
    
    if request.user != application.applicant and request.user != application.job.created_by:
        return redirect('home')
    
    # ...以下の処理はそのまま...
    Message.objects.filter(application=application, is_read=False).exclude(sender=request.user).update(is_read=True)
    request.user.notifications.filter(link__contains=f'/application/{application.id}/', is_read=False).update(is_read=True)
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
    # お知らせ一覧ページを開いたら、そのユーザーの未読通知をすべて既読にする
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'jobs/notifications.html', {'notifications': notifications})
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
            return redirect('profile_detail', user_id=request.user.id)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'jobs/profile_edit.html', {'form': form})

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

@user_passes_test(is_staff_user)
def admin_dashboard(request):
    pending_profiles = Profile.objects.filter(id_card_image__isnull=False, is_verified=False).exclude(id_card_image='') 
    return render(request, 'jobs/admin_dashboard.html', {'pending_profiles': pending_profiles})

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    profile.is_verified = True
    profile.save()
    return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    if profile.id_card_image:
        profile.id_card_image.delete()
    profile.save()
    return redirect('admin_dashboard')

    # jobs/views.py

@login_required
def reject_applicant(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    
    # 募集主本人かチェック
    if request.user != job.created_by:
        return redirect('home')

    # --- ここを追加：リンク切れになる古い通知を「既読」にして掃除する ---
    Notification.objects.filter(
        recipient=application.applicant,
        link__contains=f"/application/{application.id}/"
    ).update(is_read=True)
    # -------------------------------------------------------------  

    # メッセージの出し分け（採用後か採用前か）
    if application.status == 'accepted':
        message = f"「{job.title}」について、募集先の都合により誠に勝手ながら採用が取り消されました。恐れ入りますが、他の案件をご検討ください。"
        # 採用枠を1つ戻す
        job.headcount += 1
        job.is_closed = False
        job.save()
    else:
        message = f"「{job.title}」について、募集主の都合により今回は見送りとなりました。またの機会にご応募をお待ちしております。"

    # 相手にマイルドな通知を送る
    create_notification(
        recipient=application.applicant,
        message=message,
        link=f"/job/{job.id}/"
    )

    # 応募データを削除して整理する
    application.delete()
    
    return redirect('job_applicants', job_id=job.id)

def about_view(request): return render(request, 'jobs/about.html')
def terms_view(request): return render(request, 'jobs/terms.html')
def privacy_view(request): return render(request, 'jobs/privacy.html')
def law_view(request): return render(request, 'jobs/law.html')