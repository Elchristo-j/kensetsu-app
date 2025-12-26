from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Job, Application, Message
from .forms import JobForm, MessageForm

# トップページ
def home(request):
    jobs = Job.objects.order_by('-id')
    query = request.GET.get('query')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    return render(request, 'jobs/home.html', {'jobs': jobs, 'query': query})

# 詳細ページ
def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, 'jobs/job_detail.html', {'job': job})

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

# 応募機能（修正：自分への応募禁止）
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    # ★修正：もし募集主本人が応募しようとしたら、何もせず詳細に戻す
    if job.created_by == request.user:
        return redirect('job_detail', job_id=job.id)

    # 応募処理
    application, created = Application.objects.get_or_create(job=job, applicant=request.user)
    
    # チャットへ移動
    return redirect('chat_room', application_id=application.id)

# 応募者リスト（修正：他人に見せない）
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    # ★修正：募集主以外がアクセスしたら、トップへ追い返す
    if job.created_by != request.user:
        return redirect('home')

    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

# チャット機能
@login_required
def chat_room(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
   
    # セキュリティ：関係者以外立ち入り禁止
    # テストが終わったらコメントアウトを外してください
    # if request.user != application.applicant and request.user != application.job.created_by:
    #     return redirect('home')

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

# 採用機能（修正：人数カウント対応）
@login_required
def adopt_applicant(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    
    # セキュリティ：募集主以外は実行不可
    if request.user != job.created_by:
        return redirect('home')

    # すでに採用済みの人なら何もしない（二重カウント防止）
    if application.status == 'accepted':
        return redirect('job_applicants', job_id=job.id)

    # 1. この人を「採用」にする
    application.status = 'accepted'
    application.save()

    # 2. ★重要：募集人数（headcount）を1減らす
    if job.headcount > 0:
        job.headcount -= 1
        job.save()

    # 3. ★重要：もし人数が0になったら、そこで初めて「募集終了」にする
    if job.headcount <= 0:
        job.is_closed = True
        job.save()
        
        # 残っている「選考中」の人を全員「不採用」にする
        other_applications = job.applications.filter(status='applied')
        for app in other_applications:
            app.status = 'rejected'
            app.save()

    return redirect('job_applicants', job_id=job.id)