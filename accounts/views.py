import os
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Profile
from .forms import ProfileForm
from jobs.models import Job, Application

# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- 会員登録 ---
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

# --- プロフィール詳細 ---
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    
    # 1. このユーザーが投稿した募集履歴を取得
    jobs = Job.objects.filter(created_by=target_user).order_by('-created_at')
    
    # 2. このユーザーのお気に入りエリアを取得（もしモデルがある場合）
    # ※FavoriteAreaモデルのインポートが必要かもしれません
    # fav_areas = FavoriteArea.objects.filter(user=target_user)

    context = {
        'target_user': target_user,
        'jobs': jobs,              # これで「募集履歴」が届くようになります
        # 'fav_areas': fav_areas,   # これで「お気に入りエリア」が届くようになります
    }
    
    return render(request, 'accounts/profile_detail.html', context)
# --- 有料プラン選択画面の表示 ---
@login_required
def upgrade_plan_page(request):
    """プラン選択画面（upgrade.html）を表示する"""
    return render(request, 'accounts/upgrade.html')

# --- Stripe決済セッションの作成 ---
@login_required
def create_checkout_session(request, plan_type):
    """決済画面へリダイレクトする"""
    price_id = settings.STRIPE_PRICE_IDS.get(plan_type)
    
    if not price_id:
        return redirect('mypage')

    checkout_session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        success_url=request.build_absolute_uri('/accounts/mypage/') + '?success=true',
        cancel_url=request.build_absolute_uri('/accounts/mypage/') + '?canceled=true',
        metadata={'user_id': request.user.id, 'plan_type': plan_type},
    )
    
    return redirect(checkout_session.url, code=303)

# --- Stripe Webhook（決済成功時の自動ランクアップ） ---
@csrf_exempt
def stripe_webhook(request):
    """Stripeからの通知を受け取り、自動でユーザーランクを更新する"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception:
        return HttpResponse(status=400)

    # 支払い完了イベントを検知
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        plan_type = session['metadata'].get('plan_type')

        if user_id and plan_type:
            profile = Profile.objects.get(user_id=user_id)
            profile.rank = plan_type
            profile.save()

    return HttpResponse(status=200)