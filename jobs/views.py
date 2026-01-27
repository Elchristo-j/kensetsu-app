from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone 
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea, PREFECTURES
from accounts.forms import ProfileForm
from .forms import JobForm, MessageForm

# --- ヘルパー関数 ---
def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user): return user.is_authenticated and user.is_staff

# --- 1. Home & Search ---
def home(request):
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query', '')
    area_filter = request.GET.get('area', '')
    
    if query: 
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query)).distinct()
    if area_filter: 
        jobs = jobs.filter(prefecture=area_filter)
        
    favorites = request.user.favorite_areas.all() if request.user.is_authenticated else []
    return render(request, 'jobs/home.html', {
        'jobs': jobs, 'query': query, 'favorites': favorites, 
        'prefectures': PREFECTURES, 'page_title': '案件一覧'
    })

@login_required
def favorite_search_view(request):
    favorite_areas = request.user.favorite_areas.all()
    if not favorite_areas.exists():
        messages.info(request, "お気に入りエリアが登録されていません。")
        return redirect('profile_detail', user_id=request.user.id)
    query = Q()
    for area in favorite_areas:
        if area.city: query |= Q(prefecture=area.prefecture, city=area.city)
        else: query |= Q(prefecture=area.prefecture)
    jobs = Job.objects.filter(query).filter(is_closed=False).order_by('-id')
    return render(request, 'jobs/home.html', {
        'jobs': jobs, 'favorites': favorite_areas, 
        'prefectures': PREFECTURES, 'page_title': 'お気に入りエリアの案件'
    })

# --- 2. Job Detail & Actions ---
def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    is_applied = Application.objects.filter(job=job, applicant=request.user).exists() if request.user.is_authenticated else False
    return render(request, 'jobs/job_detail.html', {'job': job, 'is_applied': is_applied})

@login_required
def create_job(request):
    profile = request.user.profile
    if not profile.can_post_job():
        limit = profile.posting_limit
        rank_display = profile.display_rank
        if limit == 0:
            messages.error(request, f"現在のランク（{rank_display}）では募集投稿はできません。")
        else:
            messages.error(request, f"現在のランク（{rank_display}）の募集投稿上限（月{limit}件）を超えています。")
        return redirect('profile_detail', user_id=request.user.id)
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            j = form.save(commit=False); j.created_by = request.user; j.save(); return redirect('home')
    else: form = JobForm()
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': False})

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user: return redirect('home')
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid(): form.save(); return redirect('job_detail', job_id=job.id)
    else: form = JobForm(instance=job)
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': True})

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user: job.delete()
    return redirect('home')

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if not request.user.profile.can_apply():
        # display_rankを使用
        r = request.user.profile.display_rank
        l = request.user.profile.monthly_limit
        messages.error(request, f"応募上限です。現在のランク（{r}）の枠は月{l}件です。")
        return redirect('job_detail', job_id=job.id)
    Application.objects.get_or_create(job=job, applicant=request.user)
    create_notification(job.created_by, f"「{job.title}」に応募がありました。", f"/job/{job.id}/applicants/")
    return redirect('job_detail', job_id=job.id)

@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    Application.objects.filter(job=job, applicant=request.user).delete()
    return redirect('job_detail', job_id=job.id)

# --- 3. Management ---
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user: return redirect('home')
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': job.applications.all()})

@login_required
def adopt_applicant(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by: app.status = 'accepted'; app.save()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def reject_applicant(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by: app.delete()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def chat_room(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False); m.application, m.sender = app, request.user; m.save()
            receiver = app.job.created_by if request.user == app.applicant else app.applicant
            create_notification(receiver, f"{request.user.username}様からのメッセージ", f"/application/{app.id}/chat/")
            return redirect('chat_room', application_id=app.id)
    Message.objects.filter(application=app, is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'jobs/chat_room.html', {'application': app, 'form': MessageForm(), 'messages': app.messages.all()})

@login_required
def notifications(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'jobs/notifications.html', {'notifications': request.user.notifications.all().order_by('-created_at')})

# --- 4. Profile & Settings ---
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    from .models import Job, Application # 循環参照回避
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    
    # --- カウンター計算 (修正版) ---
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # created_at__gte を使用（Applicationモデルにapplied_atがない場合の対策として一般的にcreated_atを使います）
    posts_this_month = Job.objects.filter(created_by=target_user, created_at__gte=month_start).count()
    
    # 修正: applied_at が存在しない場合は created_at を使用してください
    try:
        applies_this_month = Application.objects.filter(applicant=target_user, created_at__gte=month_start).count()
    except:
        # 万が一モデルのフィールド名が applied_at の場合
        applies_this_month = Application.objects.filter(applicant=target_user, applied_at__gte=month_start).count()
    
    context = {
        'target_user': target_user, 
        'jobs': jobs, 
        'prefectures': PREFECTURES,
        'posts_this_month': posts_this_month,     
        'applies_this_month': applies_this_month
    }
    return render(request, 'accounts/profile_detail.html', context)

@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        # ★重要: request.FILES を忘れると画像が保存されません
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid(): 
            form.save()
            messages.success(request, 'プロフィールを更新しました。')
            return redirect('profile_detail', user_id=request.user.id)
    else: 
        form = ProfileForm(instance=profile)
    return render(request, 'jobs/profile_edit.html', {'form': form})

@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        p = request.POST.get('prefecture'); c = request.POST.get('city', '')
        if p: FavoriteArea.objects.get_or_create(user=request.user, prefecture=p, city=c)
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    get_object_or_404(FavoriteArea, id=area_id, user=request.user).delete()
    return redirect('profile_detail', user_id=request.user.id)

# --- 5. Admin & Static ---
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    p = Profile.objects.filter(is_verified=False, id_card_image__isnull=False).exclude(id_card_image='')
    return render(request, 'jobs/admin_dashboard.html', {'pending_profiles': p})

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile; p.is_verified = True; p.save(); return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile; p.id_card_image.delete(); p.save(); return redirect('admin_dashboard')

def about_view(request): return render(request, 'jobs/about.html')
def terms_view(request): return render(request, 'jobs/terms.html')
def privacy_view(request): return render(request, 'jobs/privacy.html')
def law_view(request): return render(request, 'jobs/law.html')