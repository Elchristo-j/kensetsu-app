import stripe
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# モデル・フォームのインポート
from accounts.models import Profile, FavoriteArea, PREFECTURES
from accounts.forms import ProfileForm
from .models import Job, Application, Message, Notification, JOB_CATEGORIES
from .forms import JobForm, MessageForm

# --- ヘルパー関数 ---
def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

# --- 1. Home & Search ---

def home(request):
    """トップページ：31日以内の新着案件を表示"""
    expiration_date = timezone.now() - timedelta(days=31)
    
    # 31日以内 かつ 募集終了していない案件
    jobs = Job.objects.filter(
        created_at__gte=expiration_date
    ).order_by('-created_at')

    favorites = []
    if request.user.is_authenticated:
        favorites = request.user.favorite_areas.all()

    context = {
        'jobs': jobs,
        'prefectures': PREFECTURES,
        'categories': JOB_CATEGORIES,
        'favorites': favorites,
    }
    return render(request, 'jobs/home.html', context)

def job_list(request):
    """検索一覧ページ：31日以内の案件を検索・表示"""
    expiration_date = timezone.now() - timedelta(days=31)
    
    # ベース：31日以内の案件
    jobs = Job.objects.filter(
        created_at__gte=expiration_date
    ).order_by('-created_at')
    
    # --- 検索フィルター ---
    query = request.GET.get('q')
    prefecture = request.GET.get('prefecture')
    category = request.GET.get('category')

    if query:
        jobs = jobs.filter(title__icontains=query)
    
    if prefecture:
        jobs = jobs.filter(prefecture=prefecture)
        
    if category:
        jobs = jobs.filter(category=category)
    
    context = {
        'jobs': jobs,
        'categories': JOB_CATEGORIES,
        'prefectures': PREFECTURES,
    }
    return render(request, 'jobs/job_list.html', context)

@login_required
def favorite_search_view(request):
    """お気に入りエリアの案件検索"""
    favorite_areas = request.user.favorite_areas.all()
    if not favorite_areas.exists():
        messages.info(request, "お気に入りエリアが登録されていません。")
        return redirect('profile_detail', user_id=request.user.id)
    
    query = Q()
    for area in favorite_areas:
        if area.city:
            query |= Q(prefecture=area.prefecture, city=area.city)
        else:
            query |= Q(prefecture=area.prefecture)
            
    # 期限切れも考慮する場合はここにも created_at フィルターを追加可能ですが、
    # お気に入りは「通知」に近い意味合いもあるため、一旦全件表示としています
    jobs = Job.objects.filter(query).filter(is_closed=False).order_by('-id')
    
    return render(request, 'jobs/home.html', {
        'jobs': jobs, 
        'favorites': favorite_areas, 
        'prefectures': PREFECTURES, 
        'categories': JOB_CATEGORIES,
        'page_title': 'お気に入りエリアの案件'
    })

# --- 2. Job Detail & Actions ---

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    is_applied = False
    if request.user.is_authenticated:
        is_applied = Application.objects.filter(job=job, applicant=request.user).exists()
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
            j = form.save(commit=False)
            j.created_by = request.user
            j.save()
            return redirect('home')
    else: 
        form = JobForm()
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': False})

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user:
        return redirect('home')
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': True})

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user:
        job.delete()
    return redirect('home')

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if not request.user.profile.can_apply():
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
    if job.created_by != request.user:
        return redirect('home')
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': job.applications.all()})

@login_required
def adopt_applicant(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by:
        app.status = 'accepted'
        app.save()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def reject_applicant(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by:
        app.delete()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def chat_room(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.application = app
            m.sender = request.user
            m.save()
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
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    
    context = {
        'target_user': target_user, 
        'jobs': jobs, 
        'prefectures': PREFECTURES,
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
        p = request.POST.get('prefecture')
        c = request.POST.get('city', '')
        if p:
            FavoriteArea.objects.get_or_create(user=request.user, prefecture=p, city=c)
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
    p = get_object_or_404(User, pk=user_id).profile
    p.is_verified = True
    p.save()
    return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile
    p.id_card_image.delete()
    p.save()
    return redirect('admin_dashboard')

def about_view(request): return render(request, 'jobs/about.html')
def terms_view(request): return render(request, 'jobs/terms.html')
def privacy_view(request): return render(request, 'jobs/privacy.html')
def law_view(request): return render(request, 'jobs/law.html')
def guide_view(request): return render(request, 'jobs/guide_qa.html')
def subscription_plans(request): return render(request, 'jobs/subscription_plans.html')

# --- 6. Stripe Payment ---

@csrf_exempt
def stripe_webhook(request):
    """Stripeからの決済完了通知を受け取り、ランクを更新する"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        amount_total = session.get('amount_total')

        if client_reference_id:
            try:
                user = User.objects.get(id=client_reference_id)
                profile = user.profile
                
                if amount_total == 550:
                    profile.rank = 'silver'
                elif amount_total == 2200:
                    profile.rank = 'gold'
                elif amount_total == 5500:
                    profile.rank = 'platinum'
                
                profile.save()
                
            except User.DoesNotExist:
                pass
            except Exception as e:
                pass

    return HttpResponse(status=200)

@login_required
def payment_success(request):
    """決済完了後に戻ってくる場所"""
    messages.success(request, 'お支払いが完了しました！ランク情報は間もなく更新されます。')
    return redirect('profile_detail', user_id=request.user.id)