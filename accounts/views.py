import os
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# フォームとモデルのインポート
from .forms import CustomUserCreationForm, ProfileForm
from .models import Profile, FavoriteArea, PREFECTURES
from jobs.models import Job, Application

# Stripe APIキーの設定
stripe.api_key = settings.STRIPE_SECRET_KEY

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
    # プロフィールがなければ作成
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # 【Render対策】サーバー再起動による画像消失時のリンク切れガード
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
            # 編集後はマイページへ戻る
            return redirect('mypage')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

# --- マイページ（評価・ランク表示対応） ---
@login_required
def mypage(request):
    # プロフィール取得
    profile = request.user.profile
    
    # ★追加: 自分の評価スタッツを取得（レーダーチャート用）
    stats = profile.get_worker_stats()

    my_applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    my_posted_jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'user': request.user,
        'profile': profile,   # ランク表示に必要
        'stats': stats,       # 評価チャートに必要
        'my_applications': my_applications,
        'my_posted_jobs': my_posted_jobs,
    }
    return render(request, 'accounts/mypage.html', context)

# --- プロフィール詳細（他人を見る時も評価を表示） ---
@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    # プロフィール取得（なければ自動作成）
    profile, _ = Profile.objects.get_or_create(user=target_user)
    
    # ★追加: 対象ユーザーの評価スタッツを取得
    stats = profile.get_worker_stats()
    
    jobs = Job.objects.filter(created_by=target_user).order_by('-created_at')
    
    context = {
        'target_user': target_user,
        'profile': profile,   # 追加
        'stats': stats,       # 追加
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
    # マイページへ戻すのが自然かもしれません（適宜調整してください）
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