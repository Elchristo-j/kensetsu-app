from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # ★検索機能用
from .models import Job, Application, Message
from .forms import JobForm, MessageForm

# トップページ（検索機能付き）
def home(request):
    # すべての仕事を取得（新しい順）
    jobs = Job.objects.order_by('-id')
    
    # 検索機能
    query = request.GET.get('query')
    if query:
        # タイトル(title) または 内容(description) にキーワードが含まれるものを探す
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

# 応募する機能（応募したらチャットへ）
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    
    # 応募データを作成（または取得）
    application, created = Application.objects.get_or_create(job=job, applicant=request.user)
    
    # チャットルームへ移動
    return redirect('chat_room', application_id=application.id)

# 応募者リストを見る機能
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

# チャットルーム機能
@login_required
def chat_room(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
   
    # セキュリティ：関係ない人は見ちゃダメ（応募者本人か、募集主だけ）
    # ★一時的に無効化中
    # if request.user != application.applicant and request.user != application.job.created_by:
    #     return redirect('home')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            message.save()
            # 投稿したら同じページを再読み込みして更新
            return redirect('chat_room', application_id=application_id)
    else:
        form = MessageForm()
    
    return render(request, 'jobs/chat_room.html', {'application': application, 'form': form})

# ★ここが今回追加するパーツです！「採用機能」
@login_required
def adopt_applicant(request, application_id):
    application = get_object_or_404(Application, pk=application_id)
    job = application.job
    
    # セキュリティ：募集主以外は勝手に採用できないようにする
    if request.user != job.created_by:
        return redirect('home')

    # 1. この応募者を「採用(accepted)」にする
    application.status = 'accepted'
    application.save()

    # 2. 他の応募者は自動的に「不採用(rejected)」にする
    other_applications = job.applications.exclude(id=application_id)
    for app in other_applications:
        app.status = 'rejected'
        app.save()

    # 3. 仕事自体を「募集終了(is_closed)」にする
    # (モデルにis_closedがある場合のみ実行)
    if hasattr(job, 'is_closed'):
        job.is_closed = True
        job.save()

    # 終わったら応募者リストに戻る
    return redirect('job_applicants', job_id=job.id)