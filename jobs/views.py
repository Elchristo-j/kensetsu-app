from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea, PREFECTURES
from accounts.forms import ProfileForm
from .forms import JobForm, MessageForm

def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user): return user.is_authenticated and user.is_staff

# --- 1. HOME (地域検索のエラーを修正) ---
def home(request):
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query', '')
    area_filter = request.GET.get('area', '')
    
    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query)).distinct()
    
    # ★修正：location ではなく prefecture でフィルター
    if area_filter:
        jobs = jobs.filter(prefecture=area_filter)
    
    favorites = []
    if request.user.is_authenticated:
        favorites = request.user.favorite_areas.all()

    return render(request, 'jobs/home.html', {
        'jobs': jobs, 
        'query': query, 
        'favorites': favorites,
        'prefectures': PREFECTURES
    })

# --- 2. 制限付き応募 (ランク名の誤表示も修正) ---
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if not request.user.profile.can_apply():
        r = request.user.profile.display_rank
        l = request.user.profile.monthly_limit
        messages.error(request, f"応募上限に達しました。現在のランク（{r}）の枠は月{l}件です。")
        return redirect('job_detail', job_id=job.id)
    Application.objects.get_or_create(job=job, applicant=request.user)
    create_notification(job.created_by, f"「{job.title}」に応募がありました。", f"/job/{job.id}/applicants/")
    return redirect('job_detail', job_id=job.id)

# --- 3. 制限付き募集投稿 ---
@login_required
def create_job(request):
    if not request.user.profile.can_post_job():
        messages.error(request, f"現在のランク（{request.user.profile.display_rank}）では募集投稿ができません。")
        return redirect('profile_detail', user_id=request.user.id)
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            j = form.save(commit=False); j.created_by = request.user; j.save(); return redirect('home')
    else: form = JobForm()
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': False})

# --- 以下、全機能を維持 ---
@login_required
def chat_room(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False); m.application, m.sender = app, request.user; m.save()
            receiver = app.job.created_by if request.user == app.applicant else app.applicant
            create_notification(receiver, f"{request.user.username}さんからのメッセージ", f"/application/{app.id}/chat/")
            return redirect('chat_room', application_id=app.id)
    Message.objects.filter(application=app, is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'jobs/chat_room.html', {'application': app, 'form': MessageForm(), 'messages': app.messages.all()})

@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    from .models import Job
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    return render(request, 'accounts/profile_detail.html', {'target_user': target_user, 'jobs': jobs, 'prefectures': PREFECTURES})

@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        p = request.POST.get('prefecture')
        if p: FavoriteArea.objects.get_or_create(user=request.user, prefecture=p)
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    get_object_or_404(FavoriteArea, id=area_id, user=request.user).delete()
    return redirect('profile_detail', user_id=request.user.id)

# (その他の関数は前回通り全て含めてください)