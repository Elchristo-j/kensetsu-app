import os
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
# ★修正点1：CustomUserを削除し、標準のUserを使う
from django.contrib.auth.models import User 
from .models import Profile, FavoriteArea, PREFECTURES
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg

# フォームとモデルのインポート
from .forms import CustomUserCreationForm, ProfileForm
# Reviewモデルが必要なのでjobsから読み込みます
from jobs.models import Job, Application, Review

# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- 共通で使う集計関数 ---
def calculate_stats(user, review_type):
    """
    指定されたユーザーと評価タイプ（ワーカー評価or発注者評価）に基づいて
    チャート用データと平均スコアを計算する関数
    """
    reviews = Review.objects.filter(target=user, review_type=review_type)
    
    if reviews.exists():
        avg_score = reviews.aggregate(Avg('score'))['score__avg']
        avg_score = round(avg_score, 1)
        
        ability = reviews.aggregate(Avg('ability'))['ability__avg'] or 0
        cooperation = reviews.aggregate(Avg('cooperation'))['cooperation__avg'] or 0
        diligence = reviews.aggregate(Avg('diligence'))['diligence__avg'] or 0
        character = reviews.aggregate(Avg('character'))['character__avg'] or 0
        utility = reviews.aggregate(Avg('utility_score'))['utility_score__avg'] or 0
        
        chart_data = [ability, cooperation, diligence, character, utility]
        
        utility_amount = reviews.aggregate(Avg('utility_amount'))['utility_amount__avg'] or 0

        return {
            'exists': True,
            'count': reviews.count(),
            'average': avg_score,
            'utility_amount': int(utility_amount),
            'chart_data': chart_data
        }
    else:
        return {
            'exists': False,
            'count': 0,
            'average': 0,
            'utility_amount': 0,
            'chart_data': [0, 0, 0, 0, 0]
        }


# --- 会員登録 ---
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

# --- プロフィールの編集 ---
@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # 【Render対策】画像消失時のリンク切れガード
    for attr in ['avatar', 'id_card_image']: 
        img_field = getattr(profile, attr, None)
        if img_field:
            try:
                if not os.path.exists(img_field.path):
                    setattr(profile, attr, None)
                    profile.save()
            except (ValueError, FileNotFoundError):
                setattr(profile, attr, None)
                profile.save()

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('mypage')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

# --- マイページ ---
@login_required
def mypage(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # 1. ワーカーとしての評価を取得
    worker_stats = calculate_stats(user, 'employer_to_worker')
    
    # 2. 発注者としての評価を取得
    employer_stats = calculate_stats(user, 'worker_to_employer')

    # 履歴データの取得
    my_posted_jobs = Job.objects.filter(created_by=user).order_by('-created_at')[:5]
    my_applications = Application.objects.filter(applicant=user).order_by('-applied_at')[:5]

    context = {
        'user': user,
        'profile': profile,
        'worker_stats': worker_stats,
        'employer_stats': employer_stats,
        'my_posted_jobs': my_posted_jobs,
        'my_applications': my_applications,
    }
    return render(request, 'accounts/mypage.html', context)

# --- プロフィール詳細（他人を見るページ） ---
@login_required
def profile_detail(request, user_id):
    # ★修正点2：CustomUser -> User に変更
    target_user = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=target_user)

    worker_stats = calculate_stats(target_user, 'employer_to_worker')
    employer_stats = calculate_stats(target_user, 'worker_to_employer')
    
    jobs = Job.objects.filter(created_by=target_user).order_by('-created_at')

    context = {
        'target_user': target_user,
        'profile': profile,
        'worker_stats': worker_stats,
        'employer_stats': employer_stats,
        'jobs': jobs,
        'prefectures': PREFECTURES,
    }
    return render(request, 'accounts/profile_detail.html', context)

# --- お気に入りエリアの追加 ---
@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        prefecture = request.POST.get('prefecture')
        city = request.POST.get('city')
        if prefecture:
            FavoriteArea.objects.create(
                user=request.user,
                prefecture=prefecture,
                city=city
            )
    return redirect('profile_detail', user_id=request.user.id)

# --- お気に入りエリアの削除 ---
@login_required
def delete_favorite_area(request, area_id):
    area = get_object_or_404(FavoriteArea, id=area_id, user=request.user)
    area.delete()
    return redirect('profile_detail', user_id=request.user.id)

# --- 有料プラン選択画面 ---
@login_required
def upgrade_plan_page(request):
    return render(request, 'accounts/upgrade.html')

# --- Stripe決済セッション作成 ---
@login_required
def create_checkout_session(request, plan_type):
    price_id = settings.STRIPE_PRICE_IDS.get(plan_type)
    
    if not price_id:
        return redirect('mypage')

    user_email = request.user.email if request.user.email else None

    checkout_session = stripe.checkout.Session.create(
        customer_email=user_email,
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        success_url=request.build_absolute_uri('/jobs/payment/success/'),
        cancel_url=request.build_absolute_uri('/jobs/plan/'),
        metadata={
            'user_id': request.user.id,
            'plan_type': plan_type
        },
        client_reference_id=str(request.user.id)
    )
    
    return redirect(checkout_session.url, code=303)

# --- Stripe Webhook ---
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id') or session['metadata'].get('user_id')
        amount_total = session.get('amount_total')
        plan_type = session['metadata'].get('plan_type')

        if user_id:
            try:
                # ★修正点3：CustomUser -> User に変更
                user = User.objects.get(id=user_id)
                profile = user.profile
                
                if plan_type:
                    profile.rank = plan_type
                elif amount_total == 550:
                    profile.rank = 'silver'
                elif amount_total == 2200:
                    profile.rank = 'gold'
                elif amount_total == 5500:
                    profile.rank = 'platinum'
                
                profile.save()
            except User.DoesNotExist:
                pass

    return HttpResponse(status=200)