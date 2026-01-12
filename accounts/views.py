import os
# ファイルの上のほうに追加
from .forms import CustomUserCreationForm
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# モデルのインポート
from .models import Profile, FavoriteArea, PREFECTURES
from .forms import ProfileForm
from jobs.models import Job, Application


# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY


# --- 会員登録 ---
def signup(request):
    if request.method == 'POST':
       # ここを CustomUserCreationForm に変更
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        # ここも CustomUserCreationForm に変更
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

# --- プロフィールの編集（Render画像消失対策込み） ---
@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Render対策：サーバー再起動による画像消失時のガード
    for attr in ['image', 'id_card_image']:
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
            return redirect('profile_detail', user_id=request.user.id)
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

# --- マイページ ---
@login_required
def mypage(request):
    my_applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    my_posted_jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'my_applications': my_applications,
        'my_posted_jobs': my_posted_jobs,
    }
    return render(request, 'accounts/mypage.html', context)

# --- プロフィール詳細（データ復旧版） ---
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    
    # 募集履歴
    jobs = Job.objects.filter(created_by=target_user).order_by('-created_at')
    
    # お気に入りエリア
    fav_areas = FavoriteArea.objects.filter(user=target_user)

    context = {
        'target_user': target_user,
        'jobs': jobs,
        'fav_areas': fav_areas,
        'prefectures': PREFECTURES, # models.pyから読み込んだリスト
    }
    return render(request, 'accounts/profile_detail.html', context)

# --- お気に入りエリアの追加（追加） ---
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

# --- お気に入りエリアの削除（追加） ---
@login_required
def delete_favorite_area(request, area_id):
    area = get_object_or_404(FavoriteArea, id=area_id, user=request.user)
    area.delete()
    return redirect('profile_detail', user_id=request.user.id)

# --- 有料プラン選択画面の表示 ---
@login_required
def upgrade_plan_page(request):
    return render(request, 'accounts/upgrade.html')

# --- Stripe決済セッションの作成 ---
# accounts/views.py の該当箇所を探して修正してください

@login_required
def create_checkout_session(request, plan_type):
    price_id = settings.STRIPE_PRICE_IDS.get(plan_type)
    
    if not price_id:
        return redirect('mypage')

    # メアドが空の場合は None を渡すようにガードをかける
    user_email = request.user.email if request.user.email else None

    checkout_session = stripe.checkout.Session.create(
        customer_email=user_email,  # 修正：空文字を避ける
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        success_url=request.build_absolute_uri('/accounts/mypage/') + '?success=true',
        cancel_url=request.build_absolute_uri('/accounts/mypage/') + '?canceled=true',
        metadata={'user_id': request.user.id, 'plan_type': plan_type},
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
        user_id = session['metadata'].get('user_id')
        plan_type = session['metadata'].get('plan_type')

        if user_id and plan_type:
            profile = Profile.objects.get(user_id=user_id)
            profile.rank = plan_type
            profile.save()

    return HttpResponse(status=200)