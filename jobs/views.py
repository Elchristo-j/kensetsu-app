from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea # ★FavoriteAreaを追加
from .forms import JobForm, MessageForm, ProfileForm

# --- 通知作成の補助関数 ---
def create_notification(recipient, message, link=None):
    """通知を生成する共通ロジック"""
    Notification.objects.create(recipient=recipient, message=message, link=link)

# --- お仕事関連 ---

def home(request):
    """トップページ：募集中の仕事を検索・一覧表示（お気に入りフィルター対応）"""
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query', '')
    area_filter = request.GET.get('area_filter', '') # ★お気に入りフィルターの取得

    # ★お気に入りエリアで絞り込むロジック
    if area_filter == 'favorites' and request.user.is_authenticated:
        fav_areas = request.user.favorite_areas.all()
        if fav_areas.exists():
            q_objects = Q()
            for area in fav_areas:
                # 市区町村があれば「県+市」、なければ「県全体」で検索
                if area.city:
                    q_objects |= Q(prefecture=area.prefecture, city__icontains=area.city)
                else:
                    q_objects |= Q(prefecture=area.prefecture)
            jobs = jobs.filter(q_objects)
        else:
            # お気に入り登録がない場合は空にするか、何もしない（今回はメッセージを出すためにそのまま）
            pass

    # 検索窓のクエリ（キーワード検索）
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
    """詳細ページ：仕事内容を表示"""
    job = get_object_or_404(Job, pk=job_id)
    is_applied = False
    if request.user.is_authenticated:
        is_applied = Application.objects.filter(job=job, applicant=request.user).exists()
    return render(request, 'jobs/job_detail.html', {'job': job, 'is_applied': is_applied})

@login_required
def create_job(request):
    """仕事作成ページ"""
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
    """お仕事編集機能"""
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
    """仕事の削除"""
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user:
        job.delete()
    return redirect('home')

# --- お気に入りエリア管理機能 ---

@login_required
def add_favorite_area(request):
    """お気に入りエリアの追加"""
    if request.method == 'POST':
        pref = request.POST.get('prefecture')
        city = request.POST.get('city', '').strip()
        if pref:
            # 重複登録を防ぎつつ作成
            FavoriteArea.objects.get_or_create(
                user=request.user, 
                prefecture=pref, 
                city=city
            )
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    """お気に入りエリアの削除"""
    area = get_object_or_404(FavoriteArea, id=area_id, user=request.user)
    area.delete()
    return redirect('profile_detail', user_id=request.user.id)

# --- 応募・採用関連 ---

@login_required
def apply_job(request, job_id):
    """応募機能"""
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        application, created = Application.objects.get_or_create(job=job, applicant=request.user)
        if created:
            create_notification(
                job.created_by, 
                f"「{job.title}」に新しい応募がありました。", 
                f"/job/{job.id}/applicants/"
            )
        return redirect('chat_room', application_id=application.id)
    return redirect('job_detail', job_id=job.id)

@login_required
def cancel_application(request, job_id):
    """応募キャンセル機能"""
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
    """応募者リスト（投稿者専用）"""
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        return redirect('home')
    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

@login_required
def adopt_applicant(request, application_id):
    """採用決定"""
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    if request.user == job.created_by and application.status != 'accepted':
        application.status = 'accepted'
        application.save()
        
        create_notification(
            application.applicant, 
            f"「{job.title}」に採用されました！チャットで詳細を確認しましょう。", 
            f"/application/{application.id}/chat/"
        )

        if job.headcount > 0:
            job.headcount -= 1
            if job.headcount <= 0:
                job.is_closed = True
                job.applications.filter(status='applied').update(status='rejected')
            job.save()
    return redirect('job_applicants', job_id=job.id)

# --- コミュニケーション ---

@login_required
def chat_room(request, application_id):
    """チャットルーム"""
    application = get_object_or_404(Application, pk=application_id)
    if request.user != application.applicant and request.user != application.job.created_by:
        return redirect('home')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            message.save()
            
            recipient = application.job.created_by if request.user == application.applicant else application.applicant
            create_notification(
                recipient, 
                f"{request.user.username}さんからメッセージがあります。", 
                f"/application/{application.id}/chat/"
            )
            return redirect('chat_room', application_id=application_id)
    else:
        form = MessageForm()
    return render(request, 'jobs/chat_room.html', {'application': application, 'form': form})

# --- 通知・プロフィール ---

@login_required
def notifications(request):
    """通知一覧ページ"""
    user_notifications = request.user.notifications.all().order_by('-created_at')
    user_notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'jobs/notifications.html', {'notifications': user_notifications})

@login_required
def profile_detail(request, user_id):
    """プロフィール詳細ページ（お気に入りエリア一覧を表示）"""
    target_user = get_object_or_404(User, pk=user_id)
    profile, created = Profile.objects.get_or_create(user=target_user)
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    
    # ★お気に入りエリアをテンプレートに渡す
    fav_areas = target_user.favorite_areas.all()
    from accounts.models import PREFECTURES # フォーム表示用
    
    return render(request, 'jobs/profile_detail.html', {
        'target_user': target_user, 
        'jobs': jobs,
        'fav_areas': fav_areas,
        'prefectures': PREFECTURES
    })

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