from accounts.models import PREFECTURES
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone 
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea, PREFECTURES
from accounts.forms import ProfileForm
from .forms import JobForm, MessageForm
# jobs/views.py の冒頭に追加が必要なインポート
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from .models import Job, JOB_CATEGORIES # JOB_CATEGORIESをインポートに追加

def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    
    # --- 検索フィルター機能 ---
    
    # キーワード検索
    query = request.GET.get('q')
    if query:
        jobs = jobs.filter(title__icontains=query)

    # 【追加】 業種での絞り込み
    category = request.GET.get('category')
    if category:
        jobs = jobs.filter(category=category)

    # 【追加】 エリア（都道府県）での絞り込み
    prefecture = request.GET.get('prefecture')
    if prefecture:
        jobs = jobs.filter(prefecture=prefecture)
    
    context = {
        'jobs': jobs,
        'categories': JOB_CATEGORIES, # テンプレートで選択肢を表示するために渡す
        'prefectures': PREFECTURES,   # accounts.modelsからインポートが必要
    }
    return render(request, 'jobs/job_list.html', context)

# --- ヘルパー関数 ---
def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user): return user.is_authenticated and user.is_staff

# --- 1. Home & Search ---
def home(request):
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query', '')
    area_filter = request.GET.get('area', '')
    
    if query: 
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query)).distinct()
    if area_filter: 
        jobs = jobs.filter(prefecture=area_filter)
        
    favorites = request.user.favorite_areas.all() if request.user.is_authenticated else []
    return render(request, 'jobs/home.html', {
        'jobs': jobs, 'query': query, 'favorites': favorites, 
        'prefectures': PREFECTURES, 'page_title': '案件一覧'
    })

@login_required
def favorite_search_view(request):
    favorite_areas = request.user.favorite_areas.all()
    if not favorite_areas.exists():
        messages.info(request, "お気に入りエリアが登録されていません。")
        return redirect('profile_detail', user_id=request.user.id)
    query = Q()
    for area in favorite_areas:
        if area.city: query |= Q(prefecture=area.prefecture, city=area.city)
        else: query |= Q(prefecture=area.prefecture)
    jobs = Job.objects.filter(query).filter(is_closed=False).order_by('-id')
    return render(request, 'jobs/home.html', {
        'jobs': jobs, 'favorites': favorite_areas, 
        'prefectures': PREFECTURES, 'page_title': 'お気に入りエリアの案件'
    })

# --- 2. Job Detail & Actions ---
def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    is_applied = Application.objects.filter(job=job, applicant=request.user).exists() if request.user.is_authenticated else False
    return render(request, 'jobs/job_detail.html', {'job': job, 'is_applied': is_applied})

@login_required
def create_job(request):
    profile = request.user.profile
    if not profile.can_post_job():
        limit = profile.posting_limit
        rank_display = profile.display_rank
        if limit == 0:
            messages.error(request, f"現在のランク（{rank_display}）では募集投稿はできません。")
        else:
            messages.error(request, f"現在のランク（{rank_display}）の募集投稿上限（月{limit}件）を超えています。")
        return redirect('profile_detail', user_id=request.user.id)
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            j = form.save(commit=False); j.created_by = request.user; j.save(); return redirect('home')
    else: form = JobForm()
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': False})

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user: return redirect('home')
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid(): form.save(); return redirect('job_detail', job_id=job.id)
    else: form = JobForm(instance=job)
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': True})

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user: job.delete()
    return redirect('home')

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if not request.user.profile.can_apply():
        # display_rankを使用
        r = request.user.profile.display_rank
        l = request.user.profile.monthly_limit
        messages.error(request, f"応募上限です。現在のランク（{r}）の枠は月{l}件です。")
        return redirect('job_detail', job_id=job.id)
    Application.objects.get_or_create(job=job, applicant=request.user)
    create_notification(job.created_by, f"「{job.title}」に応募がありました。", f"/job/{job.id}/applicants/")
    return redirect('job_detail', job_id=job.id)

@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    Application.objects.filter(job=job, applicant=request.user).delete()
    return redirect('job_detail', job_id=job.id)

# --- 3. Management ---
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user: return redirect('home')
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': job.applications.all()})

@login_required
def adopt_applicant(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by: app.status = 'accepted'; app.save()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def reject_applicant(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by: app.delete()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def chat_room(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False); m.application, m.sender = app, request.user; m.save()
            receiver = app.job.created_by if request.user == app.applicant else app.applicant
            create_notification(receiver, f"{request.user.username}様からのメッセージ", f"/application/{app.id}/chat/")
            return redirect('chat_room', application_id=app.id)
    Message.objects.filter(application=app, is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'jobs/chat_room.html', {'application': app, 'form': MessageForm(), 'messages': app.messages.all()})

@login_required
def notifications(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'jobs/notifications.html', {'notifications': request.user.notifications.all().order_by('-created_at')})

# --- 4. Profile & Settings ---
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    from .models import Job, Application # 循環参照回避
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    
    # カウンター計算は現在無効化しています（テンプレート側では '-' を表示）
    # 将来的に実装する場合はここで計算ロジックを追加してください
    
    context = {
        'target_user': target_user, 
        'jobs': jobs, 
        'prefectures': PREFECTURES,
        # カウンター変数は渡さず、テンプレートのdefault表示に任せるか、
        # 明示的にNoneを渡しても良いです
    }
    return render(request, 'accounts/profile_detail.html', context)

@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid(): 
            form.save()
            messages.success(request, 'プロフィールを更新しました。')
            return redirect('profile_detail', user_id=request.user.id)
    else: 
        form = ProfileForm(instance=profile)
    return render(request, 'jobs/profile_edit.html', {'form': form})

@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        p = request.POST.get('prefecture'); c = request.POST.get('city', '')
        if p: FavoriteArea.objects.get_or_create(user=request.user, prefecture=p, city=c)
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    get_object_or_404(FavoriteArea, id=area_id, user=request.user).delete()
    return redirect('profile_detail', user_id=request.user.id)

# --- 5. Admin & Static & New Pages ---
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    p = Profile.objects.filter(is_verified=False, id_card_image__isnull=False).exclude(id_card_image='')
    return render(request, 'jobs/admin_dashboard.html', {'pending_profiles': p})

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile; p.is_verified = True; p.save(); return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile; p.id_card_image.delete(); p.save(); return redirect('admin_dashboard')

def about_view(request): return render(request, 'jobs/about.html')
def terms_view(request): return render(request, 'jobs/terms.html')
def privacy_view(request): return render(request, 'jobs/privacy.html')
def law_view(request): return render(request, 'jobs/law.html')

# 【追加】 Q&A・ガイドページ
def guide_view(request):
    return render(request, 'jobs/guide_qa.html')

# 【追加】 プラン・解約ページ
def subscription_plans(request):
    return render(request, 'jobs/subscription_plans.html')

# 【ファイルの末尾に追加してください】

@csrf_exempt
def stripe_webhook(request):
    """Stripeからの決済完了通知を受け取り、ランクを更新する"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    
    # settings.py に STRIPE_WEBHOOK_SECRET が設定されている前提
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return HttpResponse(status=400) # Invalid payload
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400) # Invalid signature

    # 決済完了イベントのみ処理
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # テンプレートで埋め込んだ user.id を取得
        client_reference_id = session.get('client_reference_id')
        amount_total = session.get('amount_total') # 支払い金額 (例: 550)

        if client_reference_id:
            try:
                user = User.objects.get(id=client_reference_id)
                # Profileモデルの rank フィールドを更新
                # ※モデルのフィールド名が 'rank' 以外(display_rank等)の場合はここを修正してください
                profile = user.profile
                
                # 金額に応じてランク判定
                if amount_total == 550:
                    profile.rank = 'silver'
                elif amount_total == 2200:
                    profile.rank = 'gold'
                elif amount_total == 5500:
                    profile.rank = 'platinum'
                
                profile.save()
                print(f"User {user.username} upgraded to {profile.rank}")
                
            except User.DoesNotExist:
                print("User not found for ID:", client_reference_id)
            except Exception as e:
                print("Error updating profile:", e)

    return HttpResponse(status=200)
# jobs/views.py の一番最後に追加

@login_required
def payment_success(request):
    """決済完了後に戻ってくる場所"""
    messages.success(request, 'お支払いが完了しました！ランク情報は間もなく更新されます。')
    # 自分のマイページへ転送
    return redirect('profile_detail', user_id=request.user.id)