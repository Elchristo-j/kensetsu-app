from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import ProfileForm
# ★他のアプリ(jobs)からデータを持ってくるためのインポート
from jobs.models import Job, Application 

# 会員登録
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

# プロフィールの編集
@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('mypage') # ★編集後はマイページに戻るように変更
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

# ★追加：マイページ（ダッシュボード）
@login_required
def mypage(request):
    # 1. 自分が「応募した」履歴（新しい順）
    my_applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    
    # 2. 自分が「募集した」仕事（新しい順）
    my_posted_jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')

    context = {
        'my_applications': my_applications,
        'my_posted_jobs': my_posted_jobs,
    }
    return render(request, 'accounts/mypage.html', context)