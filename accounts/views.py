import os
import stripe
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
    reviews = Review.objects.filter(reviewee=user, review_type=review_type)
    count = reviews.count()
    is_hidden = count < 3 # 3件未満は隠す

    if count > 0:
        if review_type == 'employer_to_worker':
            # ワーカー評価項目
            p1 = reviews.aggregate(Avg('ability'))['ability__avg'] or 0
            p2 = reviews.aggregate(Avg('cooperation'))['cooperation__avg'] or 0
            p3 = reviews.aggregate(Avg('diligence'))['diligence__avg'] or 0
            p4 = reviews.aggregate(Avg('humanity'))['humanity__avg'] or 0
            p5 = reviews.aggregate(Avg('utility_score'))['utility_score__avg'] or 0
            labels = ['能力', '協調性', '勤勉性', '人間性', '有用性']
            wage_range = calculate_utility_wage_text(p5)
            chart_data = [p1, p2, p3, p4, p5]

        else:
            # 発注者評価項目
            p1 = reviews.aggregate(Avg('working_hours'))['working_hours__avg'] or 0
            p2 = reviews.aggregate(Avg('reward'))['reward__avg'] or 0
            p3 = reviews.aggregate(Avg('job_content'))['job_content__avg'] or 0
            p4 = reviews.aggregate(Avg('preparation'))['preparation__avg'] or 0
            p5 = reviews.aggregate(Avg('credibility'))['credibility__avg'] or 0
            labels = ['作業時間', '報酬', '仕事内容', '段取り', '信用性']
            wage_range = None # 発注者には日当なし
            chart_data = [p1, p2, p3, p4, p5]

        avg_score = sum(chart_data) / 5

        return {
            'exists': True,
            'is_hidden': is_hidden,
            'count': count,
            'average': round(avg_score, 1),
            'chart_data': chart_data,
            'labels': labels,
            'wage_range': wage_range,
        }
    else:
        return {
            'exists': False,
            'is_hidden': True,
            'count': 0,
            'average': 0,
            'chart_data': [0,0,0,0,0],
            'labels': [],
            'wage_range': None
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
    # Render画像消失対策
    for attr in ['avatar', 'id_card_image']: 
        img = getattr(profile, attr, None)
        if img and not os.path.exists(img.path): setattr(profile, attr, None)
    
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

    context = {
        'user': request.user, 'profile': profile,
        'worker_stats': worker_stats, 'employer_stats': employer_stats,
        'my_posted_jobs': my_posted, 'my_applications': my_applied,
    }
    return render(request, 'accounts/mypage.html', context)

@login_required
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
        success_url=request.build_absolute_uri('/jobs/payment/success/'),
        cancel_url=request.build_absolute_uri('/jobs/plan/'),
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
                p = User.objects.get(id=uid).profile
                if ptype: p.rank = ptype
                p.save()
            except: pass
    return HttpResponse(status=200)