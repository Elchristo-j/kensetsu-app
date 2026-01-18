from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Job, Application, Message, Notification
from accounts.models import Profile, FavoriteArea, PREFECTURES
from accounts.forms import ProfileForm
from .forms import JobForm, MessageForm

def create_notification(recipient, message, link=None):
    Notification.objects.create(recipient=recipient, message=message, link=link)

def is_staff_user(user): return user.is_authenticated and user.is_staff

def home(request):
    jobs = Job.objects.filter(is_closed=False).order_by('-id')
    query = request.GET.get('query', '')
    if query: jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query)).distinct()
    return render(request, 'jobs/home.html', {'jobs': jobs, 'query': query})

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    is_applied = Application.objects.filter(job=job, applicant=request.user).exists() if request.user.is_authenticated else False
    return render(request, 'jobs/job_detail.html', {'job': job, 'is_applied': is_applied})

@login_required
def create_job(request):
    # 【執行】募集投稿ができるランクかチェック
    if not request.user.profile.can_post_job():
        messages.error(request, f"現在のランク（{request.user.profile.display_rank}）では案件の募集はできません。ランクアップをご検討ください。")
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
        messages.error(request, f"今月の応募上限（{request.user.profile.monthly_limit}件）に達しました。")
        return redirect('job_detail', job_id=job.id)
    Application.objects.get_or_create(job=job, applicant=request.user)
    return redirect('job_detail', job_id=job.id)

@login_required
def cancel_application(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    Application.objects.filter(job=job, applicant=request.user).delete()
    return redirect('job_detail', job_id=job.id)

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
    return render(request, 'jobs/chat_room.html', {'application': app, 'form': MessageForm()})

@login_required
def notifications(request):
    return render(request, 'jobs/notifications.html', {'notifications': request.user.notifications.all().order_by('-created_at')})

@login_required
def profile_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    jobs = Job.objects.filter(created_by=target_user).order_by('-id')
    return render(request, 'accounts/profile_detail.html', {'target_user': target_user, 'jobs': jobs, 'prefectures': PREFECTURES})

@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid(): form.save(); return redirect('profile_detail', user_id=request.user.id)
    else: form = ProfileForm(instance=profile)
    return render(request, 'jobs/profile_edit.html', {'form': form})

@login_required
def add_favorite_area(request):
    if request.method == 'POST':
        p, c = request.POST.get('prefecture'), request.POST.get('city', '').strip()
        if p: FavoriteArea.objects.get_or_create(user=request.user, prefecture=p, city=c)
    return redirect('profile_detail', user_id=request.user.id)

@login_required
def delete_favorite_area(request, area_id):
    get_object_or_404(FavoriteArea, id=area_id, user=request.user).delete()
    return redirect('profile_detail', user_id=request.user.id)

@user_passes_test(is_staff_user)
def admin_dashboard(request):
    pending = Profile.objects.filter(is_verified=False, id_card_image__isnull=False).exclude(id_card_image='')
    return render(request, 'jobs/admin_dashboard.html', {'pending_profiles': pending})

@user_passes_test(is_staff_user)
def approve_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile; p.is_verified = True; p.save()
    return redirect('admin_dashboard')

@user_passes_test(is_staff_user)
def reject_profile(request, user_id):
    p = get_object_or_404(User, pk=user_id).profile; p.id_card_image.delete(); p.save()
    return redirect('admin_dashboard')

def about_view(request): return render(request, 'jobs/about.html')
def terms_view(request): return render(request, 'jobs/terms.html')
def privacy_view(request): return render(request, 'jobs/privacy.html')
def law_view(request): return render(request, 'jobs/law.html')