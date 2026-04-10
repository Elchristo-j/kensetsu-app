from accounts.models import Profile

def app_detection(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    is_ios_app = ('elchristo-ios-app' in user_agent) or ('elchristo-android-app' in user_agent)
    
    pending_verification_count = 0
    if request.user.is_authenticated and request.user.is_superuser:
        pending_verification_count = Profile.objects.filter(
            is_verified=False,
            id_card_image__isnull=False
        ).exclude(id_card_image='').count()
    
    return {
        'is_ios_app': is_ios_app,
        'pending_verification_count': pending_verification_count,
    }