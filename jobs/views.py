from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Job, Application
from .forms import JobForm

def home(request):
    """募集中の仕事を検索・一覧表示"""
    jobs = Job.objects.filter(is_closed=False).order_by('-created_at')
    query = request.GET.get('query', '')
    
    if query:
        # 都道府県、市区町村、タイトル、詳細から横断検索
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(prefecture__icontains=query) |
            Q(city__icontains=query)
        ).distinct()
    
    return render(request, 'jobs/home.html', {'jobs': jobs, 'query': query})

@login_required
def create_job(request):
    """仕事の新規作成（保存を確実に行う）"""
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