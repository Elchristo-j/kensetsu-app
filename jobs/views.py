from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User # ★追加：ユーザー情報を扱うため
from .models import Job, Application, Message
from .forms import JobForm, MessageForm

# トップページ（募集中のものだけ表示）
def home(request):
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
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
    if job.created_by != request.user:
        return redirect('home')
    job.delete()
    return redirect('home')

# 応募機能
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user:
        return redirect('job_detail', job_id=job.id)
    application, created = Application.objects.get_or_create(job=job, applicant=request.user)
    return redirect('chat_room', application_id=application.id)

# 応募キャンセル機能
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

# 応募者リスト
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        return redirect('home')
    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

# チャットルーム
@login_required
def chat_room(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
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

# 採用機能
@login_required
def adopt_applicant(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    if request.user != job.created_by:
        return redirect('home')
    if application.status == 'accepted':
        return redirect('job_applicants', job_id=job.id)
    application.status = 'accepted'
    application.save()
    if job.headcount > 0:
        job.headcount -= 1
        job.save()
    if job.headcount <= 0:
        job.is_closed = True
        job.save()
        other_applications = job.applications.filter(status='applied')
        for app in other_applications:
            app.status = 'rejected'
            app.save()
    return redirect('job_applicants', job_id=job.id)

# ★新規追加：プロフィール詳細機能
@login_required
def profile_detail(request, user_id):
    # 見たいユーザーの情報を取得
    target_user = get_object_or_404(User, pk=user_id)
    
    # そのユーザーが作成した過去の案件（新しい順）
    jobs = Job.objects.filter(created_by=target_user).order_by('-created_at')

    return render(request, 'jobs/profile_detail.html', {
        'target_user': target_user,
        'jobs': jobs
    })