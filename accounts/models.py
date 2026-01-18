from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=100, blank=True, verbose_name="表示名")
    location = models.CharField(max_length=100, blank=True, verbose_name="地域")
    description = models.TextField(blank=True, verbose_name="自己紹介")
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    id_card_image = models.ImageField(upload_to='id_cards/', blank=True, null=True)
    rank = models.CharField(max_length=20, default='iron')

    @property
    def display_rank(self): return 'bronze' if self.is_verified and self.rank == 'iron' else self.rank
    @property
    def rank_class(self): return f"badge-{self.display_rank}"
    @property
    def monthly_limit(self):
        r = self.display_rank.lower()
        return 3 if r in ['iron', 'bronze'] else 999
    def can_apply(self):
        from jobs.models import Application
        count = Application.objects.filter(applicant=self.user, applied_at__gte=timezone.now().replace(day=1, hour=0, minute=0, second=0)).count()
        return count < self.monthly_limit if isinstance(self.monthly_limit, int) else True