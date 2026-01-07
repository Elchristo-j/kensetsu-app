# jobs/context_processors.py

from accounts.models import Profile

def pending_verification_count(request):
    """
    全てのページで「本人確認の承認待ち人数」を使えるようにする
    """
    if request.user.is_authenticated and request.user.is_staff:
        # 身分証があって、かつ未承認の人数を数える
        count = Profile.objects.filter(
            id_card_image__isnull=False, 
            is_verified=False
        ).exclude(id_card_image='').count()
        return {'pending_count': count}
    
    return {'pending_count': 0}