@login_required
def notifications(request):
    # チャット以外の通知だけを既読にする
    request.user.notifications.filter(is_read=False).exclude(link__contains='chat').update(is_read=True)
    
    # 全通知を取得して表示
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'jobs/notifications.html', {'notifications': notifications})

@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    Profile.objects.get_or_create(user=target_user)
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    fav_areas = target_user.favorite_areas.all()
    from accounts.models import PREFECTURES
    return render(request, 'jobs/profile_detail.html', {'target_user': target_user, 'jobs': jobs, 'fav_areas': fav_areas, 'prefectures': PREFECTURES})

@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if 'id_card_image' in request.FILES:
                try:
                    send_mail(
                        subject="【重要】本人確認の申請が届きました",
                        message=f"{request.user.username} さんから身分証画像が届きました。",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.EMAIL_HOST_USER],
                        fail_silently=True,
                    )
                except:
                    pass
            return redirect('profile_detail', user_id=request.user.id)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'jobs/profile_edit.html', {'form': form})

# --- 運営専用ダッシュボード機能 ---

@user_passes_test(is_staff_user)
def admin_dashboard(request):
    pending_profiles = Profile.objects.filter(
        id_card_image__isnull=False, 
        is_verified=False
    ).exclude(id_card_image='') 
    return render(request, 'jobs/admin_dashboard.html', {'pending_profiles': pending_profiles})

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    profile.is_verified = True
    profile.save()
    create_notification(target_user, "🎉 本人確認が承認されました！", f"/profile/{target_user.id}/")
    return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile = target_user.profile
    if profile.id_card_image:
        profile.id_card_image.delete()
    profile.save()
    create_notification(target_user, "⚠️ 本人確認書類に不備がありました。再アップロードをお願いします。", "/accounts/profile/edit/")
    return redirect('admin_dashboard')

# --- 規約・情報ページ（ここが左端に揃っていることが重要です） ---

def about_view(request):
    return render(request, 'jobs/about.html')

def terms_view(request):
    return render(request, 'jobs/terms.html')

def privacy_view(request):
    return render(request, 'jobs/privacy.html')

def law_view(request):
    return render(request, 'jobs/law.html')