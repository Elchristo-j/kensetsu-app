from accounts.models import Profile
from config.utils import is_app_request

def app_detection(request):
    # 判定ロジックは config.utils.is_app_request に一本化（ビューからも同じ判定を使う）
    is_ios_app = is_app_request(request)

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