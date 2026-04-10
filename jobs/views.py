import stripe
from datetime import timedelta, date
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# アカウント関連のモデル・フォーム
from accounts.models import Profile, FavoriteArea, PREFECTURES, Block
from accounts.forms import ProfileForm
from accounts.views import mypage, profile_detail, profile_edit

# ジョブ関連のモデル・フォーム
from .models import (
    Job, Application, Message, Notification, Review, News, 
    WorkerAvailability, UraProfile, JOB_CATEGORIES, Scout, EPointHistory
)
from .forms import JobForm, MessageForm, ContactForm, UraProfileForm, ScoutForm

# --- ヘルパー関数 ---
def get_blocked_user_ids(user):
    if not user.is_authenticated:
        return []
    blocking = Block.objects.filter(blocker=user).values_list('blocked_id', flat=True)
    blocked_by = Block.objects.filter(blocked=user).values_list('blocker_id', flat=True)
    return list(blocking) + list(blocked_by)

def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def calculate_stats_for_user(user, review_type):
    if review_type == 'employer_to_worker':
        reviews = Review.objects.filter(reviewee=user, review_type='employer_to_worker')
        if not reviews.exists(): return None
        return {
            'ability': reviews.aggregate(Avg('ability'))['ability__avg'],
            'cooperation': reviews.aggregate(Avg('cooperation'))['cooperation__avg'],
            'diligence': reviews.aggregate(Avg('diligence'))['diligence__avg'],
            'humanity': reviews.aggregate(Avg('humanity'))['humanity__avg'],
            'utility_score': reviews.aggregate(Avg('utility_score'))['utility_score__avg'],
            'count': reviews.count()
        }
    else:
        reviews = Review.objects.filter(reviewee=user, review_type='worker_to_employer')
        if not reviews.exists(): return None
        return {
            'working_hours': reviews.aggregate(Avg('working_hours'))['working_hours__avg'],
            'reward': reviews.aggregate(Avg('reward'))['reward__avg'],
            'job_content': reviews.aggregate(Avg('job_content'))['job_content__avg'],
            'preparation': reviews.aggregate(Avg('preparation'))['preparation__avg'],
            'credibility': reviews.aggregate(Avg('credibility'))['credibility__avg'],
            'count': reviews.count()
        }
    
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            if request.user.is_authenticated:
                contact.user = request.user
            contact.save()
            messages.success(request, 'お問い合わせを受け付けました。確認後ご連絡いたします。')
            return redirect('home')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.profile.company_name or request.user.username,
                'email': request.user.email
            }
        form = ContactForm(initial=initial_data)
    
    return render(request, 'jobs/contact.html', {'form': form})

# --- 1. Home & Search ---
def home(request):
    expiration_date = timezone.now() - timedelta(days=31)
    jobs = Job.objects.filter(is_closed=False, created_at__gte=expiration_date).order_by('-created_at')
    news_list = News.objects.filter(is_published=True).order_by('-created_at')[:3]
    
    if request.user.is_authenticated:
        ignore_ids = get_blocked_user_ids(request.user)
        if ignore_ids:
            jobs = jobs.exclude(created_by__id__in=ignore_ids)

    favorites = []
    if request.user.is_authenticated:
        favorites = request.user.favorite_areas.all()
    context = {'jobs': jobs, 'latest_jobs': jobs, 'prefectures': PREFECTURES, 'categories': JOB_CATEGORIES, 'favorites': favorites, 'news_list': news_list}
    return render(request, 'jobs/home.html', context)

def job_list(request):
    expiration_date = timezone.now() - timedelta(days=31)
    jobs = Job.objects.filter(created_at__gte=expiration_date, is_closed=False).order_by('-created_at')

    if request.user.is_authenticated:
        ignore_ids = get_blocked_user_ids(request.user)
        if ignore_ids:
            jobs = jobs.exclude(created_by__id__in=ignore_ids)

    query = request.GET.get('q')
    prefecture = request.GET.get('prefecture')
    category = request.GET.get('category')

    if query:
        jobs = jobs.filter(title__icontains=query)
    if prefecture:
        jobs = jobs.filter(prefecture=prefecture)
    if category:
        jobs = jobs.filter(category=category)

    return render(request, 'jobs/job_list.html', {
        'jobs': jobs, 
        'categories': JOB_CATEGORIES, 
        'prefectures': PREFECTURES
    })

@login_required
def favorite_search_view(request):
    favorite_areas = request.user.favorite_areas.all()
    if not favorite_areas.exists():
        messages.info(request, "お気に入りエリアが登録されていません。")
        return redirect('mypage')
    
    query = Q()
    for area in favorite_areas:
        if area.city: query |= Q(prefecture=area.prefecture, city=area.city)
        else: query |= Q(prefecture=area.prefecture)
    
    jobs = Job.objects.filter(query).filter(is_closed=False).order_by('-id')

    ignore_ids = get_blocked_user_ids(request.user)
    if ignore_ids:
        jobs = jobs.exclude(created_by__id__in=ignore_ids)

    return render(request, 'jobs/home.html', {'jobs': jobs, 'favorites': favorite_areas, 'prefectures': PREFECTURES, 'categories': JOB_CATEGORIES, 'page_title': 'お気に入りエリアの案件'})

# --- 2. Job Detail & Actions ---
def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    
    if request.user.is_authenticated:
        if Block.objects.filter(blocker=request.user, blocked=job.created_by).exists() or \
           Block.objects.filter(blocker=job.created_by, blocked=request.user).exists():
            messages.warning(request, "この案件は表示できません。")
            return redirect('home')

    application = None
    is_applied = False
    if request.user.is_authenticated:
        application = Application.objects.filter(job=job, applicant=request.user).first()
        is_applied = (application is not None)
    
    can_apply = False
    limit_info = 0
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        can_apply = request.user.profile.can_apply()
        limit_info = request.user.profile.monthly_limit
    
    if request.method == 'POST':
        if not request.user.is_authenticated: return redirect('login')
        if not is_applied and can_apply and not job.is_closed:
            new_app = Application.objects.create(job=job, applicant=request.user)
            messages.success(request, '応募が完了しました！')
            return redirect('job_detail', job_id=job.id)
        else:
            messages.error(request, '応募できませんでした（制限超過、すでに応募済み、または募集終了）')

    context = {
        'job': job, 
        'is_applied': is_applied, 
        'application': application,
        'can_apply': can_apply, 
        'limit_info': limit_info
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
def create_job(request):
    profile = request.user.profile
    if not profile.can_post_job():
        limit = profile.posting_limit
        messages.error(request, f"募集投稿の上限（月{limit}件）を超えています。")
        return redirect('mypage')
    
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
    if job.created_by != request.user: return redirect('home')
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
    if job.created_by == request.user: job.delete()
    return redirect('home')

# ▼▼▼ 追加：手動で募集を終了し、トップ画面から消すための処理 ▼▼▼
@login_required
def close_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by == request.user:
        job.is_closed = True
        job.save()
        messages.success(request, '案件の募集を終了しました。トップ画面からも非表示になります。')
    return redirect('job_detail', job_id=job.id)
# ▲▲▲ 追加ここまで ▲▲▲

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    # ▼▼▼ 修正：募集終了した案件への直接応募をシステム側で完全ブロック ▼▼▼
    if job.is_closed:
        messages.error(request, "この案件はすでに募集を終了しているため、応募できません。")
        return redirect('job_detail', job_id=job.id)
    # ▲▲▲ 修正ここまで ▲▲▲

    if not request.user.profile.can_apply():
        l = request.user.profile.monthly_limit
        messages.error(request, f"応募上限です。現在のランクの枠は月{l}件です。")
        return redirect('job_detail', job_id=job.id)
        
    Application.objects.get_or_create(job=job, applicant=request.user)
    create_notification(job.created_by, f"「{job.title}」に応募がありました。", f"/job/{job.id}/applicants/")
    return redirect('job_detail', job_id=job.id)

@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    app = Application.objects.filter(job=job, applicant=request.user).first()
    if app:
        chat_link_part = f"/application/{app.id}/"
        Notification.objects.filter(link__contains=chat_link_part).delete()
        
        app.status = 'canceled'
        app.save()
        create_notification(job.created_by, f"案件「{job.title}」で{request.user.username}さんが辞退しました。", f"/application/{app.id}/chat/")
            
        messages.info(request, "応募を辞退しました。")
    return redirect('job_detail', job_id=job.id)

# --- 3. Management & Contract Flow ---
@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if job.created_by != request.user: return redirect('home')
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
        app.status = 'rejected'
        app.save()
    return redirect('job_applicants', job_id=app.job.id)

@login_required
def contract_application(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    if request.user == app.job.created_by: 
        if app.status == 'canceled':
            messages.error(request, "この応募者はすでに辞退しています。契約はできません。")
            return redirect('chat_room', application_id=app.id)
            
        if app.status == 'accepted':
            app.status = 'contracted'
            app.save()

            EPointHistory.objects.create(
                user=app.job.created_by,
                action_type='job_contracted',
                points=1,
                description=f"案件「{app.job.title}」の契約成立",
                related_job=app.job,
                related_application=app
            )

            create_notification(app.applicant, f"案件「{app.job.title}」の契約が成立しました！", f"/application/{app.id}/chat/")
            messages.success(request, "契約が成立しました。業務を開始できます。Eポイントを1pt獲得しました！")

            job = app.job
            filled_count = job.applications.filter(status__in=['contracted', 'completed']).count()
            
            if filled_count >= job.headcount:
                job.is_closed = True
                job.save()
                
                leftover_apps = job.applications.filter(status__in=['pending', 'accepted'])
                
                for leftover in leftover_apps:
                    leftover.status = 'rejected'
                    leftover.save()
                    create_notification(
                        leftover.applicant, 
                        f"案件「{job.title}」は募集枠が埋まったため、今回は見送りとなりました。またの機会にお願いいたします。", 
                        f"/job/{job.id}/"
                    )
            
    return redirect('chat_room', application_id=app.id)

@login_required
def complete_job_work(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    
    if request.user != app.job.created_by:
        messages.error(request, "業務完了の手続きは発注者（依頼主）のみが行えます。")
        return redirect('chat_room', application_id=app.id)

    if app.status == 'contracted':
        app.status = 'completed'
        app.save()

        EPointHistory.objects.create(
            user=app.job.created_by,
            action_type='job_completed',
            points=3,
            description=f"案件「{app.job.title}」の業務完了",
            related_job=app.job,
            related_application=app
        )
        messages.success(request, "業務を完了としました。Eポイントを3pt獲得しました！相互評価を行ってください。")

        create_notification(app.applicant, f"案件「{app.job.title}」が完了しました。評価をお願いします。", f"/application/{app.id}/chat/")
        
    return redirect('chat_room', application_id=app.id)

@login_required
def submit_review(request, application_id):
    app = get_object_or_404(Application, pk=application_id)
    
    if request.method == 'POST':
        if request.user == app.job.created_by:
            review_type = 'employer_to_worker'
            reviewee = app.applicant
        else:
            review_type = 'worker_to_employer'
            reviewee = app.job.created_by
        
        if Review.objects.filter(job=app.job, reviewer=request.user, reviewee=reviewee).exists():
            messages.error(request, "すでに評価済みです。")
            return redirect('chat_room', application_id=app.id)
        
        p1 = int(request.POST.get('p1', 3))
        p2 = int(request.POST.get('p2', 3))
        p3 = int(request.POST.get('p3', 3))
        p4 = int(request.POST.get('p4', 3))
        p5 = int(request.POST.get('p5', 3)) 
        comment = request.POST.get('comment', '')

        Review.objects.create(
            reviewer=request.user,
            reviewee=reviewee,
            job=app.job,
            review_type=review_type,
            ability=p1, cooperation=p2, diligence=p3, humanity=p4, utility_score=p5,
            working_hours=p1, reward=p2, job_content=p3, preparation=p4, credibility=p5,
            comment=comment
        )

        EPointHistory.objects.create(
            user=request.user,
            action_type='review_given',
            points=1,
            description=f"「{app.job.title}」の相手を評価しました",
            related_job=app.job,
            related_application=app
        )
        EPointHistory.objects.create(
            user=reviewee,
            action_type='review_received',
            points=1,
            description=f"「{app.job.title}」で評価されました",
            related_job=app.job,
            related_application=app
        )

        messages.success(request, "評価を送信し、Eポイントを1pt獲得しました！")
    
    return redirect('chat_room', application_id=app.id)

@login_required
def chat_room(request, application_id):
    try:
        app = Application.objects.get(pk=application_id)
    except Application.DoesNotExist:
        messages.warning(request, "このチャットルームは存在しないか、応募がキャンセルされました。")
        return redirect('mypage')
        
    if request.user != app.applicant and request.user != app.job.created_by:
        return redirect('home')

    # ▼▼▼ 修正：無効なチャットルームに入ろうとした時の500エラーを撃退 ▼▼▼
    if app.status in ['canceled', 'rejected']:
        messages.error(request, "この応募は見送り、またはキャンセルされたため、チャットルームは利用できません。")
        return redirect('job_detail', job_id=app.job.id)

    if app.job.is_closed and app.status not in ['contracted', 'completed']:
        messages.error(request, "この案件はすでに募集が終了しています。")
        return redirect('job_detail', job_id=app.job.id)
    # ▲▲▲ 修正ここまで ▲▲▲

    if request.method == 'POST' and 'content' in request.POST:
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
    
    target_user = app.job.created_by if request.user == app.applicant else app.applicant
    has_reviewed = Review.objects.filter(job=app.job, reviewer=request.user, reviewee=target_user).exists()
    
    context = {
        'application': app, 
        'form': MessageForm(), 
        'messages': app.messages.all(),
        'has_reviewed': has_reviewed
    }
    return render(request, 'jobs/chat_room.html', context)

@login_required
def notifications(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'jobs/notifications.html', {'notifications': request.user.notifications.all().order_by('-created_at')})


@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        p = request.POST.get('prefecture')
        c = request.POST.get('city', '')
        if p:
            FavoriteArea.objects.get_or_create(user=request.user, prefecture=p, city=c)
    return redirect('mypage')

@login_required
def delete_favorite_area(request, area_id):
    get_object_or_404(FavoriteArea, id=area_id, user=request.user).delete()
    return redirect('mypage')

# --- 5. Admin & Static & New Pages ---
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    p = Profile.objects.filter(is_verified=False, id_card_image__isnull=False).exclude(id_card_image='')
    return render(request, 'jobs/admin_dashboard.html', {'pending_profiles': p})

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile
    p.is_verified = True
    if p.rank == 'iron':
        p.rank = 'bronze'
    p.save()
    return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        custom_message = request.POST.get('custom_message', '')
        
        # メール送信
        full_message = reason
        if custom_message:
            full_message += f'\n\n【詳細】\n{custom_message}'
        
        from django.core.mail import send_mail
        send_mail(
            subject='【El\'christo】本人確認書類の不備について',
            message=f'''{p.user.username} 様

本人確認書類を確認しましたが、以下の理由により再提出をお願いいたします。

【不備の理由】
{full_message}

お手数ですが、プロフィール編集画面から再度書類をアップロードしてください。
ご不明な点はお問い合わせページからご連絡ください。

建設マッチング El'christo 運営局''',
            from_email=None,
            recipient_list=[p.user.email],
            fail_silently=True,
        )
        
        p.id_card_image.delete()
        p.save()
        return redirect('admin_dashboard')
    
    return render(request, 'jobs/reject_profile.html', {'profile': p})

def about_view(request): return render(request, 'jobs/static_pages/about.html')
def terms_view(request): return render(request, 'jobs/static_pages/terms.html')
def privacy_view(request): return render(request, 'jobs/static_pages/privacy.html')
def law_view(request): return render(request, 'jobs/static_pages/law.html')
def guide_view(request): return render(request, 'jobs/guide_qa.html')

def subscription_plans(request):
    if not request.user.is_authenticated:
        messages.warning(request, "プランの確認・変更にはログインが必要です。")
        return redirect('login')
    if request.user.profile.rank == 'iron':
        return render(request, 'accounts/verification_required.html')
    return render(request, 'jobs/subscription_plans.html')

# --- 6. Stripe Payment ---
@csrf_exempt
def stripe_webhook(request):
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
                if amount_total == 550: profile.rank = 'silver'
                elif amount_total == 2200: profile.rank = 'gold'
                elif amount_total == 5500: profile.rank = 'platinum'
                profile.save()
            except User.DoesNotExist: pass
            except Exception: pass

    return HttpResponse(status=200)

@login_required
def payment_success(request):
    messages.success(request, 'お支払いが完了しました！ランク情報は間もなく更新されます。')
    return redirect('mypage')

@login_required
def blocked_list(request):
    blocks = Block.objects.filter(blocker=request.user).select_related('blocked')
    return render(request, 'jobs/blocked_list.html', {'blocks': blocks})

@login_required
def unblock_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    Block.objects.filter(blocker=request.user, blocked=target).delete()
    messages.success(request, f"{target.username}さんのブロックを解除しました。")
    return redirect('blocked_list')

def news_detail(request, news_id):
    news = get_object_or_404(News, pk=news_id, is_published=True)
    return render(request, 'jobs/news_detail.html', {'news': news})

# --- 裏案件（スカウト）機能 ---
@login_required
def edit_ura_profile(request):
    if request.user.profile.rank == 'iron':
        messages.error(request, '裏案件（スカウト機能）を利用するには、本人確認が必要です。')
        return redirect('mypage')
        
    ura_profile, created = UraProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UraProfileForm(request.POST, instance=ura_profile)
        if form.is_valid():
            form.save()
            messages.success(request, '裏プロフィールを更新しました！')
            return redirect('mypage')
    else:
        form = UraProfileForm(instance=ura_profile)
        
    return render(request, 'jobs/ura_profile_edit.html', {'form': form})

@login_required
def edit_availability(request):
    if request.user.profile.rank == 'iron':
        messages.error(request, 'カレンダー機能を利用するには、本人確認が必要です。')
        return redirect('mypage')

    today = date.today()
    dates = [today + timedelta(days=i) for i in range(30)]
    
    if request.method == 'POST':
        for d in dates:
            date_str = d.strftime('%Y-%m-%d')
            status = request.POST.get(f'status_{date_str}')
            if status:
                WorkerAvailability.objects.update_or_create(
                    user=request.user,
                    date=d,
                    defaults={'status': status}
                )
        messages.success(request, 'カレンダー（空き状況）を更新しました！')
        return redirect('edit_availability')
        
    try:
        existing_availabilities = WorkerAvailability.objects.filter(user=request.user, date__in=dates)
        status_map = {ea.date: ea.status for ea in existing_availabilities}
    except Exception:
        status_map = {}
    
    calendar_data = []
    for d in dates:
        calendar_data.append({
            'date': d,
            'date_str': d.strftime('%Y-%m-%d'),
            'status': status_map.get(d, 'available')
        })
        
    return render(request, 'jobs/availability_edit.html', {'calendar_data': calendar_data})

@login_required
def ura_profile_list(request):
    if request.user.profile.rank == 'iron':
        messages.error(request, '闇市（裏案件リスト）を見るには、本人確認（BRONZE以上）が必要です。')
        return redirect('mypage')

    ura_profiles = UraProfile.objects.filter(is_published=True).exclude(user=request.user).order_by('-updated_at')
    context = {'ura_profiles': ura_profiles}
    return render(request, 'jobs/ura_profile_list.html', context)

@login_required
def ura_profile_detail(request, pk):
    if request.user.profile.rank == 'iron':
        messages.error(request, '詳細を見るには本人確認（BRONZE以上）が必要です。')
        return redirect('mypage')

    ura_profile = get_object_or_404(UraProfile, pk=pk, is_published=True)
    if ura_profile.user == request.user:
        return redirect('ura_profile_list')

    today = date.today()
    availabilities = WorkerAvailability.objects.filter(
        user=ura_profile.user,
        date__gte=today,
        date__lte=today + timedelta(days=30)
    ).order_by('date')

    context = {
        'ura_profile': ura_profile,
        'availabilities': availabilities,
    }
    return render(request, 'jobs/ura_profile_detail.html', context)
    
@login_required
def send_scout(request, pk):
    ura_profile = get_object_or_404(UraProfile, pk=pk, is_published=True)
    worker_user = ura_profile.user
    employer_user = request.user

    user_rank = employer_user.profile.rank
    limit_map = {'iron': 0, 'bronze': 0, 'silver': 3, 'gold': 10, 'platinum': 999999}
    monthly_limit = limit_map.get(user_rank, 0)

    now = timezone.now()
    scouts_this_month = Scout.objects.filter(
        employer=employer_user, created_at__year=now.year, created_at__month=now.month
    ).count()

    if scouts_this_month >= monthly_limit and user_rank != 'platinum':
        messages.error(request, f'今月のスカウト送信上限（{monthly_limit}回）に達しています。プランをアップグレードしてください。')
        return redirect('ura_profile_detail', pk=pk)

    if request.method == 'POST':
        form = ScoutForm(request.POST, employer=employer_user)
        if form.is_valid():
            scout = form.save(commit=False)
            scout.employer = employer_user
            scout.worker = worker_user
            scout.save()
            messages.success(request, f'{ura_profile.main_occupation}さんにスカウトを送信しました！')
            return redirect('ura_profile_detail', pk=pk)
    else:
        form = ScoutForm(employer=employer_user)

    scouts_left = monthly_limit - scouts_this_month if user_rank != 'platinum' else '無制限'
    context = {
        'ura_profile': ura_profile,
        'form': form,
        'scouts_left': scouts_left,
        'monthly_limit': monthly_limit if user_rank != 'platinum' else '無制限',
    }
    return render(request, 'jobs/send_scout.html', context)

@login_required
def received_scouts(request):
    scouts = Scout.objects.filter(worker=request.user).order_by('-created_at')
    context = {'scouts': scouts}
    return render(request, 'jobs/received_scouts.html', context)

@login_required
def scout_detail(request, pk):
    scout = get_object_or_404(Scout, pk=pk, worker=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            application, created = Application.objects.get_or_create(
                job=scout.target_job,
                applicant=request.user,
                defaults={'status': 'accepted'}
            )
            if not created and application.status == 'pending':
                application.status = 'accepted'
                application.save()

            EPointHistory.objects.create(
                user=scout.employer,
                action_type='scout_accepted',
                points=2,
                description=f"スカウト承諾により「{scout.target_job.title}」の交渉開始",
                related_job=scout.target_job,
                related_application=application
            )

            scout.delete()
            messages.success(request, '交渉ルームが作成されました！まずは相手に挨拶を送ってみましょう。')
            return redirect('chat_room', application_id=application.id)
            
        elif action == 'decline':
            scout.delete()
            messages.info(request, '今回はスカウトを見送りました。')
            return redirect('received_scouts')

    context = {'scout': scout}
    return render(request, 'jobs/scout_detail.html', context)
    
