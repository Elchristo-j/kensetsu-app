from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# 都道府県リスト
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
    # ランク定義
    RANK_CHOICES = [
        ('iron', 'iron'), 
        ('bronze', 'bronze'), 
        ('silver', 'silver'), 
        ('gold', 'gold'), 
        ('platinum', 'platinum'), # ← ここにカンマを追加しました
    ] # ← ここでリストを閉じます！

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 【追加】 役職フィールド（リストの外に書くのが正解です）
    position = models.CharField(max_length=100, blank=True, null=True, verbose_name="役職・部署")
    
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default='iron')
    is_verified = models.BooleanField(default=False, verbose_name="本人確認済み")
    
    # 基本情報
    company_name = models.CharField(max_length=100, blank=True, verbose_name="屋号・会社名")
    location = models.CharField(max_length=100, blank=True, choices=PREFECTURES, verbose_name="所在地")
    bio = models.TextField(blank=True, verbose_name="自己紹介")
    
    # 画像関連
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="アバター画像")
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name="旧プロフィール画像")
    id_card_image = models.ImageField(upload_to='id_cards/', blank=True, null=True, verbose_name="本人確認書類")

    # 詳細プロフィール項目
    experience_years = models.IntegerField(default=0, verbose_name="経験年数")
    qualifications = models.CharField(max_length=255, blank=True, null=True, verbose_name="保有資格")
    skills = models.CharField(max_length=255, blank=True, null=True, verbose_name="得意な工事・スキル")
    invoice_num = models.CharField(max_length=50, blank=True, null=True, verbose_name="インボイス登録番号")
    
    # 決済情報（Stripe用に追加しておくと安全です）
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- プロパティ・ロジック ---

    @property
    def display_rank(self):
        """表示上のランクを返す（Ironでも本人確認済みならBronze扱い）"""
        if self.is_verified and self.rank == 'iron':
            return 'bronze'
        return self.rank

    @property
    def rank_class(self):
        """バッジ表示用のCSSクラス名を返す"""
        return f"badge-{self.display_rank.lower()}"

    @property
    def unread_notifications_count(self):
        """未読通知数"""
        return self.user.notifications.filter(is_read=False).count()

    @property
    def monthly_limit(self):
        """今月の応募可能数（Apply）"""
        r = self.display_rank.lower()
        if r == 'iron': return 3
        if r == 'bronze': return 10
        # Silver, Gold, Platinum は無制限
        return 999 

    @property
    def posting_limit(self):
        """今月の募集投稿可能数（Post Job）"""
        r = self.display_rank.lower()
        if r in ['iron', 'bronze']: return 0
        if r == 'silver': return 3
        # Gold, Platinum は無制限
        return 999

    def can_apply(self):
        """今月応募できるか判定"""
        from jobs.models import Application
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        try:
            cnt = Application.objects.filter(applicant=self.user, applied_at__gte=start_of_month).count()
        except:
            cnt = Application.objects.filter(applicant=self.user, created_at__gte=start_of_month).count()
        return cnt < self.monthly_limit

    def can_post_job(self):
        """今月募集投稿できるか判定"""
        from jobs.models import Job
        if self.posting_limit == 0: return False
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cnt = Job.objects.filter(created_by=self.user, created_at__gte=start_of_month).count()
        return cnt < self.posting_limit
    
    def __str__(self):
        return self.user.username


class FavoriteArea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_areas')
    prefecture = models.CharField(max_length=20, choices=PREFECTURES)
    city = models.CharField(max_length=50, blank=True, null=True, default='')

    def __str__(self):
        return f"{self.user.username} - {self.prefecture}{self.city}"

# ユーザー作成時に自動でProfileを作成するシグナル
@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)