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
    for attr in ['avatar', 'id_card_image']: # image -> avatar に変更されたため修正
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
    
    # このユーザーが募集している案件を取得
    jobs = Job.objects.filter(created_by=target_user).order_by('-created_at')
    
    # テンプレートに渡すデータ
    context = {
        'target_user': target_user,
        'jobs': jobs,
        'prefectures': PREFECTURES, # エリア選択用リスト
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
    # settings.py に定義された STRIPE_PRICE_IDS からIDを取得
    price_id = settings.STRIPE_PRICE_IDS.get(plan_type)
    
    if not price_id:
        return redirect('mypage')

    user_email = request.user.email if request.user.email else None

    # Stripeの決済画面を作成
    checkout_session = stripe.checkout.Session.create(
        customer_email=user_email,
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        # 決済成功・キャンセル時の戻り先URL
        success_url=request.build_absolute_uri('/jobs/payment/success/'), # 修正済みのURL
        cancel_url=request.build_absolute_uri('/jobs/plan/'),
        metadata={
            'user_id': request.user.id,
            'plan_type': plan_type
        },
        client_reference_id=str(request.user.id) # 念のためここにも追加
    )
    
    return redirect(checkout_session.url, code=303)

# --- Stripe Webhook (自動ランク更新用) ---
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
        
        # client_reference_id または metadata からユーザーを特定
        user_id = session.get('client_reference_id') or session['metadata'].get('user_id')
        
        # 金額からランクを判定 (metadataのplan_typeがあればそれを使用、なければ金額判定)
        amount_total = session.get('amount_total')
        plan_type = session['metadata'].get('plan_type')

        if user_id:
            try:
                user = User.objects.get(id=user_id)
                profile = user.profile
                
                # プラン判定ロジック
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