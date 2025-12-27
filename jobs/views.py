from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Job, Application, Message
# accountsアプリのProfileモデルを操作するためにインポート
from accounts.models import Profile
# ProfileForm を含めたフォーム類をインポート
from .forms import JobForm, MessageForm, ProfileForm

# --- お仕事関連 ---

# トップページ（募集中のものだけ表示）
def home(request):
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query')
    if query:
        # キーワード検索（タイトル、内容、都道府県、市区町村）
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(prefecture__icontains=query) |
            Q(city__icontains=query)
        ).distinct()
    return render(request, 'jobs/home.html', {'jobs': jobs, 'query': query})

# 詳細ページ
def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    is_applied = False
    if request.user.is_authenticated:
        is_applied = Application.objects.filter(job=job, applicant=request.user).exists()
    return render(request, 'jobs/job_detail.html', {'job': job, 'is_applied': is_applied})

# 仕事作成ページ
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
    return render(request, 'jobs/create_job.html', {'form': form})

# 案件削除機能
@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    # 本人確認
    if job.created_by != request.user:
        return redirect('home')
    job.delete()
    return redirect('home')

# --- 応募・採用関連 ---

# 応募機能
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    # 自分の出した案件には応募できない
    if job.created_by == request.user:
        return redirect('job_detail', job_id=job.id)
    
    application, created = Application.objects.get_or_create(job=job, applicant=request.user)
    return redirect('chat_room', application_id=application.id)

# 応募キャンセル機能
@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    application = get_object_or_404(Application, job=job, applicant=request.user)
    # 採用済みだった場合は、募集人数を戻す
    if application.status == 'accepted':
        job.headcount += 1
        job.is_closed = False
        job.save()
    application.delete()
    return redirect('job_detail', job_id=job.id)

# 応募者リスト（投稿者専用）
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        return redirect('home')
    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

# 採用決定機能
@login_required
def adopt_applicant(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    if request.user != job.created_by:
        return redirect('home')
    
    if application.status != 'accepted':
        application.status = 'accepted'
        application.save()
        
        # 募集人数のカウントダウン
        if job.headcount > 0:
            job.headcount -= 1
            if job.headcount <= 0:
                job.is_closed = True
                # 定員に達したら他の応募者を不採用にする
                job.applications.filter(status='applied').update(status='rejected')
            job.save()
            
    return redirect('job_applicants', job_id=job.id)

# --- コミュニケーション ---

# チャットルーム
@login_required
def chat_room(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    # 投稿者か応募者本人しか入れない
    if request.user != application.applicant and request.user != application.job.created_by:
        return redirect('home')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            message.save()
            return redirect('chat_room', application_id=application_id)
    else:
        form = MessageForm()
    
    return render(request, 'jobs/chat_room.html', {'application': application, 'form': form})

# --- プロフィール・マイページ ---

# プロフィール詳細
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    # プロフィールが存在しない場合に備えて取得または作成
    profile, created = Profile.objects.get_or_create(user=target_user)
    
    # そのユーザーが作成した過去の案件
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')

    return render(request, 'jobs/profile_detail.html', {
        'target_user': target_user,
        'jobs': jobs
    })

# ★新規追加：プロフィール編集
@login_required
def profile_edit(request):
    # ログインユーザーのプロフィールを取得
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # 画像などのファイルが含まれるため request.FILES が必須
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', user_id=request.user.id)
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'jobs/profile_edit.html', {'form': form})