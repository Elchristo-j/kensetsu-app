from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # ★検索のために追加（Qオブジェクト）
from .models import Job, Application
from .forms import JobForm

# トップページ（検索機能付き）
def home(request):
    # すべての仕事を取得（新しい順）
    jobs = Job.objects.order_by('-id')
    
    # 検索機能：もしURLに 'query' というキーワードが含まれていたら...
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

# 応募する機能
@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    Application.objects.get_or_create(job=job, applicant=request.user)
    return redirect('home')

# 応募者リストを見る機能
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    applications = job.applications.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})