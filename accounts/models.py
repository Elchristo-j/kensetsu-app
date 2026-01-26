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
    RANK_CHOICES = [('iron', 'iron'), ('bronze', 'bronze'), ('SILVER', 'SILVER'), ('GOLD', 'GOLD'), ('PLATINUM', 'PLATINUM')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='iron')
    is_verified = models.BooleanField(default=False)
    company_name = models.CharField(max_length=100, blank=True, verbose_name="表示名")
    location = models.CharField(max_length=100, blank=True, choices=PREFECTURES, verbose_name="地域")
    description = models.TextField(blank=True, verbose_name="自己紹介・実績")
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    id_card_image = models.ImageField(upload_to='id_cards/', blank=True, null=True)

    @property
    def display_rank(self):
        """見た目上のテキスト：上位は大文字、下位は小文字"""
        r = 'bronze' if self.is_verified and self.rank == 'iron' else self.rank
        return r # 文字ケースはCSSで制御するためここでは名前のみ返す

    @property
    def rank_class(self):
        """CSS用のクラス名：すべて小文字で統一"""
        return f"badge-{self.display_rank.lower()}"

    @property
    def unread_notifications_count(self):
        return self.user.notifications.filter(is_read=False).count()

    @property
    def monthly_limit(self):
        r = self.display_rank.lower()
        if r == 'iron': return 3
        if r == 'bronze': return 10
        return 999 

    @property
    def posting_limit(self):
        """募集制限：iron/bronze(0), silver(3), gold以上(無制限)"""
        r = self.display_rank.lower()
        if r in ['iron', 'bronze']: return 0
        if r == 'silver': return 3
        return 999

    def can_apply(self):
        from jobs.models import Application
        cnt = Application.objects.filter(applicant=self.user, applied_at__gte=timezone.now().replace(day=1, hour=0, minute=0)).count()
        return cnt < self.monthly_limit

    def can_post_job(self):
        from jobs.models import Job
        limit = self.posting_limit
        if limit == 0: return False
        cnt = Job.objects.filter(created_by=self.user, created_at__gte=timezone.now().replace(day=1, hour=0, minute=0)).count()
        return cnt < limit

    def __str__(self): return f"{self.user.username}のプロフィール"

class FavoriteArea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_areas')
    prefecture = models.CharField(max_length=20, choices=PREFECTURES)
    city = models.CharField(max_length=50, blank=True)

@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    if created: Profile.objects.get_or_create(user=instance)
    