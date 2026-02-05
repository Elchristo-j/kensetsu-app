from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Avg

# 都道府県リスト
PREFECTURES = [
    ('北海道', '北海道'), ('青森県', '青森県'), ('岩手県', '岩手県'), ('宮城県', '宮城県'), ('秋田県', '秋田県'), ('山形県', '山形県'), ('福島県', '福島県'),
    ('茨城県', '茨城県'), ('栃木県', '栃木県'), ('群馬県', '群馬県'), ('埼玉県', '埼玉県'), ('千葉県', '千葉県'), ('東京都', '東京都'), ('神奈川県', '神奈川県'),
    ('新潟県', '新潟県'), ('富山県', '富山県'), ('石川県', '石川県'), ('福井県', '福井県'), ('山梨県', '山梨県'), ('長野県', '長野県'), ('岐阜県', '岐阜県'),
    ('静岡県', '静岡県'), ('愛知県', '愛知県'), ('三重県', '三重県'), ('滋賀県', '滋賀県'), ('大阪府', '大阪府'), ('兵庫県', '兵庫県'),
    ('奈良県', '奈良県'), ('和歌山県', '和歌山県'), ('鳥取県', '鳥取県'), ('島根県', '島根県'), ('岡山県', '岡山県'), ('広島県', '広島県'), ('山口県', '山口県'),
    ('徳島県', '徳島県'), ('香川県', '香川県'), ('愛媛県', '愛媛県'), ('高知県', '高知県'), ('福岡県', '福岡県'), ('佐賀県', '佐賀県'), ('長崎県', '長崎県'),
    ('熊本県', '熊本県'), ('大分県', '大分県'), ('宮崎県', '宮崎県'), ('鹿児島県', '鹿児島県'), ('沖縄県', '沖縄県')
]

class Profile(models.Model):
    # ランク定義
    RANK_CHOICES = [
        ('iron', 'iron'), 
        ('bronze', 'bronze'), 
        ('silver', 'SILVER'), 
        ('gold', 'GOLD'), 
        ('platinum', 'PLATINUM'),
    ]

    # 年代の選択肢
    AGE_GROUP_CHOICES = [
        ('10s', '10代'), ('20s', '20代'), ('30s', '30代'), 
        ('40s', '40代'), ('50s', '50代'), ('60s', '60代以上'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='iron')
    is_verified = models.BooleanField(default=False, verbose_name="本人確認済み")
    
    # 基本情報
    company_name = models.CharField(max_length=100, blank=True, verbose_name="屋号・会社名")
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="役職・部署")
    age_group = models.CharField(max_length=5, choices=AGE_GROUP_CHOICES, blank=True, null=True, verbose_name="年代")
    
    # 職種（メイン・サブ）
    occupation_main = models.CharField(max_length=50, blank=True, null=True, verbose_name="メイン職種")
    occupation_sub = models.CharField(max_length=50, blank=True, null=True, verbose_name="サブ職種")
    
    location = models.CharField(max_length=100, blank=True, choices=PREFECTURES, verbose_name="所在地")
    bio = models.TextField(blank=True, verbose_name="自己紹介")
    
    # 画像
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="アバター画像")
    id_card_image = models.ImageField(upload_to='id_cards/', blank=True, null=True, verbose_name="本人確認書類")

    # 詳細プロフィール
    experience_years = models.IntegerField(default=0, verbose_name="経験年数")
    qualifications = models.CharField(max_length=255, blank=True, null=True, verbose_name="保有資格")
    skills = models.CharField(max_length=255, blank=True, null=True, verbose_name="得意な工事・スキル")
    invoice_num = models.CharField(max_length=50, blank=True, null=True, verbose_name="インボイス登録番号")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def monthly_limit(self):
        """今月の応募可能数"""
        r = str(self.rank).lower() if self.rank else 'iron'
        if r == 'iron': return 3
        if r == 'bronze': return 10
        if r in ['silver', 'gold', 'platinum']: return 999 
        return 3

    @property
    def posting_limit(self):
        """今月の募集投稿可能数"""
        r = str(self.rank).lower() if self.rank else 'iron'
        if r in ['iron', 'bronze']: return 0
        if r == 'silver': return 3
        if r in ['gold', 'platinum']: return 999
        return 0

    # ▼▼▼ 復活させたメソッド（ここがないとエラーになります） ▼▼▼
    def can_apply(self):
        """今月応募できるか判定"""
        # 循環参照避けるためここでインポート
        from jobs.models import Application 
        
        # 月初の取得
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 今月の応募数
        count = Application.objects.filter(applicant=self.user, applied_at__gte=start_of_month).count()
        
        return count < self.monthly_limit

    def can_post_job(self):
        """今月募集投稿できるか判定"""
        from jobs.models import Job
        
        limit = self.posting_limit
        if limit == 0: return False
        
        # 無制限の場合はカウント不要
        if limit >= 999: return True

        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        count = Job.objects.filter(created_by=self.user, created_at__gte=start_of_month).count()
        return count < limit
    # ▲▲▲ ここまで ▲▲▲

    def __str__(self):
        return self.user.username

class FavoriteArea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_areas')
    prefecture = models.CharField(max_length=20, choices=PREFECTURES)
    city = models.CharField(max_length=50, blank=True, null=True, default='')

    def __str__(self):
        return f"{self.user.username} - {self.prefecture}{self.city}"

@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)