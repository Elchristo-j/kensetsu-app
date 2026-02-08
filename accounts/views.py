from django.utils import timezone # ★ファイルの先頭に追加
import os
import stripe
import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile, FavoriteArea, PREFECTURES
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg

from .forms import CustomUserCreationForm, ProfileForm
from jobs.models import Job, Application, Review

stripe.api_key = settings.STRIPE_SECRET_KEY

# --- 日当換算テキスト変換 ---
def calculate_utility_wage_text(score):
    score = round(score)
    if score <= 0: return "〜3,000"
    if score == 1: return "4,000〜6,000"
    if score == 2: return "7,000〜9,000"
    if score == 3: return "10,000〜12,000"
    if score == 4: return "13,000〜15,000"
    if score == 5: return "16,000〜18,000"
    if score == 6: return "19,000〜21,000"
    if score == 7: return "22,000〜24,000"
    if score == 8: return "25,000〜27,000"
    if score == 9: return "28,000〜30,000"
    return "31,000〜"

# --- 集計関数 ---
def calculate_stats(user, review_type):

    all_reviews = Review.objects.filter(reviewee=user, review_type=review_type)
    total_count = all_reviews.count()

    # ▼ 変更点: 3件未満は問答無用で「データなし」扱い
    if total_count < 3:
        return {
            'exists': False,
            'is_hidden': True,
            'count': 0,
            'average': 0,
            'chart_data': [0, 0, 0, 0, 0],
            'labels': [],
            'wage_range': None
        }
    
    # ▼ 変更点: 3の倍数で切り捨てる計算 (例: 5 // 3 * 3 = 3,  8 // 3 * 3 = 6)
    visible_count = (total_count // 3) * 3

    # ▼ 変更点: 「古い順」に visible_count 件だけを取得して計算対象にする
    # これにより、最新の1,2件（端数）は計算から除外されるため、誰が何点をつけたかバレません。
    target_ids = all_reviews.order_by('created_at').values_list('id', flat=True)[:visible_count]
    target_reviews = Review.objects.filter(id__in=target_ids)

    # --- 以下、集計ロジックは target_reviews に対して行う ---

    
    if review_type == 'employer_to_worker':
        p1 = target_reviews.aggregate(Avg('ability'))['ability__avg'] or 0
        p2 = target_reviews.aggregate(Avg('cooperation'))['cooperation__avg'] or 0
        p3 = target_reviews.aggregate(Avg('diligence'))['diligence__avg'] or 0
        p4 = target_reviews.aggregate(Avg('humanity'))['humanity__avg'] or 0
        p5 = target_reviews.aggregate(Avg('utility_score'))['utility_score__avg'] or 0
        labels = ['能力', '協調性', '勤勉性', '人間性', '有用性']
        wage_range = calculate_utility_wage_text(p5)
        chart_data = [p1, p2, p3, p4, p5]
    else:
        p1 = target_reviews.aggregate(Avg('working_hours'))['working_hours__avg'] or 0
        p2 = target_reviews.aggregate(Avg('reward'))['reward__avg'] or 0
        p3 = target_reviews.aggregate(Avg('job_content'))['job_content__avg'] or 0
        p4 = target_reviews.aggregate(Avg('preparation'))['preparation__avg'] or 0
        p5 = target_reviews.aggregate(Avg('credibility'))['credibility__avg'] or 0
        labels = ['作業時間', '報酬', '仕事内容', '段取り', '信用性']
        wage_range = None
        chart_data = [p1, p2, p3, p4, p5]

    avg_score = sum(chart_data) / 5

    return {
        'exists': True,
        'is_hidden': False, # 3件以上あるので必ず表示
        'count': total_count, # 表示上の件数は「全件」でOK（計算だけ3の倍数）
        'average': round(avg_score, 1),
        'chart_data': chart_data,
        'labels': labels,
        'wage_range': wage_range,
    }
    
   

# --- ビュー定義 ---

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # ログインさせる
            from django.contrib.auth import login
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # ★修正: マイページへ戻る
            return redirect('mypage')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/profile_edit.html', {'form': form})

@login_required
def mypage(request):
    profile = request.user.profile
    worker_stats = calculate_stats(request.user, 'employer_to_worker')
    employer_stats = calculate_stats(request.user, 'worker_to_employer')
    my_posted = Job.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    my_applied = Application.objects.filter(applicant=request.user).order_by('-applied_at')[:5]

    # ▼▼▼ 【追加】今月の利用状況の集計 ▼▼▼
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 今月の使用数をカウント
    used_jobs = Job.objects.filter(created_by=request.user, created_at__gte=start_of_month).count()
    used_apps = Application.objects.filter(applicant=request.user, applied_at__gte=start_of_month).count()

    # ランクごとの上限設定（※仕様に合わせて書き換えてください！）
    LIMITS = {
        'iron':     {'job': 1,  'app': 3},
        'bronze':   {'job': 5,  'app': 10},
        'silver':   {'job': 10, 'app': 20},
        'gold':     {'job': 20, 'app': 50},
        'platinum': {'job': 999,'app': 999}, # 無制限
    }
    
    # 自分のランクの上限を取得（なければIron扱い）
    my_limits = LIMITS.get(profile.rank, LIMITS['iron'])
    
    # 残り回数を計算（マイナスにならないようにmax使用）
    remaining_jobs = max(0, my_limits['job'] - used_jobs)
    remaining_apps = max(0, my_limits['app'] - used_apps)
    # ▲▲▲ 【追加終わり】 ▲▲▲

    context = {
        'user': request.user, 'profile': profile,
        'worker_stats': worker_stats, 'employer_stats': employer_stats,
        'my_posted_jobs': my_posted, 'my_applications': my_applied,
        
        # HTMLで使えるように渡す
        'remaining_jobs': remaining_jobs,
        'remaining_apps': remaining_apps,
        'limit_jobs': my_limits['job'],
        'limit_apps': my_limits['app'],
    }
    return render(request, 'accounts/mypage.html', context)

    context = {
        'user': request.user, 'profile': profile,
        'worker_stats': worker_stats, 'employer_stats': employer_stats,
        'my_posted_jobs': my_posted, 'my_applications': my_applied,
    }
    return render(request, 'accounts/mypage.html', context)

def profile_detail(request, user_id):
    target = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=target)
    worker_stats = calculate_stats(target, 'employer_to_worker')
    employer_stats = calculate_stats(target, 'worker_to_employer')
    jobs = Job.objects.filter(created_by=target).order_by('-created_at')

    context = {
        'target_user': target, 'profile': profile,
        'worker_stats': worker_stats, 'employer_stats': employer_stats,
        'jobs': jobs, 'prefectures': PREFECTURES,
    }
    return render(request, 'accounts/profile_detail.html', context)

@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        pref = request.POST.get('prefecture')
        city = request.POST.get('city')
        if pref: FavoriteArea.objects.create(user=request.user, prefecture=pref, city=city)
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    get_object_or_404(FavoriteArea, id=area_id, user=request.user).delete()
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def upgrade_plan_page(request):
    return render(request, 'accounts/upgrade.html')

@login_required
def create_checkout_session(request, plan_type):
    # Stripeロジック
    price_id = settings.STRIPE_PRICE_IDS.get(plan_type)
    if not price_id: return redirect('mypage')
    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        success_url=request.build_absolute_uri('/payment/success/'),
        cancel_url=request.build_absolute_uri('/plan/'),
        metadata={'user_id': request.user.id, 'plan_type': plan_type}
    )
    return redirect(session.url, code=303)

@csrf_exempt
def stripe_webhook(request):
    # Webhookロジック
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except: return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        uid = session['metadata'].get('user_id')
        ptype = session['metadata'].get('plan_type')
        
        if uid:
            try:
                # User経由でProfileを取得するように変更
                user = User.objects.get(id=uid)
                p = user.profile
                
                # ランク更新
                if ptype: 
                    p.rank = ptype
                
                # ▼▼▼ キャンペーン自動適用ロジック ▼▼▼
                # 「有料プラン」かつ「2026年3月31日まで」なら創設メンバーにする
                today = datetime.date.today()
                campaign_end = datetime.date(2026, 3, 31)
                
                if ptype in ['silver', 'gold', 'platinum'] and today <= campaign_end:
                    p.is_founding_member = True
                
                p.save()
            except: pass
            
    return HttpResponse(status=200)