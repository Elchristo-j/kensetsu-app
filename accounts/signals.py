from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=Profile)
def upgrade_rank_on_verification(sender, instance, **kwargs):
    # 本人確認済み(is_identity_verified=True) かつ、ランクがまだIronの場合
    if instance.is_identity_verified and instance.rank == 'iron':
        instance.rank = 'bronze'
        instance.save()
        