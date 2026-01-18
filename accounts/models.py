from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

PREFECTURES = [
    ('北海道', '北海道'), ('青森県', '青森県'), ('岩手県', '岩手県'), ('宮城県', '宮城県'), ('秋田県', '秋田県'), ('山形県', '山形県'), ('福島県', '福島県'),
    ('茨城県', '茨城県'), ('栃木県', '栃木県'), ('群馬県', '群馬県'), ('埼玉県', '埼玉県'), ('千葉県', '千葉県'), ('東京都', '東京都'), ('神奈川県', '神奈川県'),
    ('新潟県', '新潟県'), ('富山県', '富山県'), ('石川県', '石川県'), ('福井県', '福井県'), ('山梨県', '山梨県'), ('長野県', '長野県'), ('岐阜県', '岐阜県'),
    ('静岡県', '静岡県'), ('愛知県', '愛知県'), ('三重県', '三重県'), ('滋賀県', '滋賀県'), ('京都府', '京都府'), ('大阪府', '大阪府'), ('兵庫県', '兵庫県'),
    ('奈良県', '奈良県'), ('和歌山県', '和歌山県'), ('鳥取県', '鳥取県'), ('島根県', '島根県'), ('岡山県', '岡山県'), ('広島県', '広島県'), ('山口県', '山口県'),
    ('徳島県', '徳島県'), ('香川県', '香川県'), ('愛媛県', '愛媛県'), ('高知県', '高知県'), ('福岡県', '福岡県'), ('佐賀県', '佐賀県'), ('長崎県', '長崎県'),
    ('熊本県', '熊本県'), ('大分県', '大分県'), ('宮崎県', '宮崎県'), ('鹿児島県', '鹿児島県'), ('沖縄県', '沖縄県')
]

class Profile(models.Model):
    RANK_CHOICES = [('iron', 'iron'), ('bronze', 'bronze'), ('SILVER', 'SILVER'), ('GOLD', 'GOLD'), ('PLATINA', 'PLATINA')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=100, blank=True, verbose_name="表示名")
    location = models.CharField(max_length=100, blank=True, choices=PREFECTURES, verbose_name="地域")
    description = models.TextField(blank=True, verbose_name="自己紹介")
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    id_card_image = models.ImageField(upload_to='id_cards/', blank=True, null=True)
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='iron')

    @property
    def display_rank(self): return 'bronze' if self.is_verified and self.rank == 'iron' else self.rank
    @property
    def rank_class(self): return f"badge-{self.display_rank}"
    @property
    def monthly_limit(self): return 3 if self.display_rank.lower() in ['iron', 'bronze'] else 999
    def can_apply(self):
        from jobs.models import Application
        cnt = Application.objects.filter(applicant=self.user, applied_at__gte=timezone.now().replace(day=1, hour=0, minute=0)).count()
        return cnt < self.monthly_limit

class FavoriteArea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_areas')
    prefecture = models.CharField(max_length=20, choices=PREFECTURES)
    city = models.CharField(max_length=50, blank=True)

@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    if created: Profile.objects.get_or_create(user=instance)

    # accounts/models.py

@property
def monthly_limit(self):
    """応募制限のロジック"""
    r = self.display_rank.lower()
    if r == 'iron': return 3
    if r == 'bronze': return 10
    return "無制限"

@property
def posting_limit(self):
    """募集投稿制限のロジック"""
    r = self.display_rank.lower()
    if r in ['iron', 'bronze']: return 0 # 投稿不可
    if r == 'silver': return 3
    return "無制限"

def can_post_job(self):
    """募集投稿ができるか判定"""
    limit = self.posting_limit
    if limit == 0: return False
    if limit == "無制限": return True
    # 今月の投稿数をカウント
    from jobs.models import Job
    count = Job.objects.filter(created_by=self.user, created_at__gte=timezone.now().replace(day=1, hour=0, minute=0)).count()
    return count < limit