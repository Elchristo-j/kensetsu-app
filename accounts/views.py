import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile
from .forms import ProfileForm
# 他のアプリ(jobs)からデータを持ってくるためのインポート
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

# プロフィールの編集（保存エラー対策済み・完全版）
@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # --- 【Render対策】保存前の自動ファイル修復ガード ---
    # データベースに画像記録があるのに、サーバー上のファイルが消えている場合、
    # Djangoが保存時にパニック（FileNotFoundError）を起こすのを防ぎます。
    if profile.image:
        try:
            if not os.path.exists(profile.image.path):
                profile.image = None
                profile.save()
        except (ValueError, FileNotFoundError):
            profile.image = None
            profile.save()

    if hasattr(profile, 'id_card_image') and profile.id_card_image:
        try:
            if not os.path.exists(profile.id_card_image.path):
                profile.id_card_image = None
                profile.save()
        except (ValueError, FileNotFoundError):
            profile.id_card_image = None
            profile.save()
    # --------------------------------------------------

    if request.method == 'POST':
        # 画像や身分証を送るために request.FILES が必須です
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', user_id=request.user.id)
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

# マイページ（ダッシュボード）
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

# プロフィール詳細（ランク表示用）
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    # 本人確認済みならアイアンでもブロンズとして表示するロジックはModel側で処理済み
    context = {
        'target_user': target_user,
    }
    return render(request, 'accounts/profile_detail.html', context)