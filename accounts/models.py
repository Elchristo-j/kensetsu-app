from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime

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
    # --- 1. ランクの選択肢を定義（ここを追加） ---
    RANK_CHOICES = [
        ('iron', 'アイアン（鉄）'),
        ('bronze', 'ブロンズ（銅）'),
        ('silver', 'シルバー（銀）'),
        ('gold', 'ゴールド（金）'),
        ('platinum', 'プラチナ'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="ユーザー")
    location = models.CharField(max_length=100, blank=True, default='', verbose_name="拠点")
    description = models.TextField(blank=True, default='', verbose_name="自己紹介・実績")
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name="アイコン画像")
    
    # 以前の is_premium も残しておいてOKです。今後は rank で管理します。
    is_premium = models.BooleanField(default=False, verbose_name="有料会員")

    # 本人確認用項目
    is_verified = models.BooleanField(default=False, verbose_name="本人確認済み")
    id_card_image = models.ImageField(upload_to='id_cards/', blank=True, null=True, verbose_name="身分証画像")
    
    # --- 2. ランク項目を追加（ここを追加） ---
    rank = models.CharField(
        max_length=20, 
        choices=RANK_CHOICES, 
        default='iron', 
        verbose_name="会員ランク"
    )

    class Meta:
        verbose_name = "プロフィール"
        verbose_name_plural = "プロフィール一覧"

    def __str__(self):
        return f"{self.user.username} のプロフィール"

    # --- 3. プロパティ類を整理 ---
    @property
    def unread_notifications_count(self):
        """未読通知の件数を取得"""
        return self.user.notifications.filter(is_read=False).count()

    @property
    def total_unread_count(self):
        """通知の未読数を返す（数字のバッジ用）"""
        return self.unread_notifications_count

    def get_monthly_application_count(self):
        """今月の応募数をカウントする"""
        from jobs.models import Application
        now = timezone.now()
        # 今月の1日 0時0分を取得
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # 自分の応募のうち、今月作成されたものを数える
        return Application.objects.filter(applicant=self.user, applied_at__gte=start_of_month).count()
        # ---------------------------------------------
    def can_apply(self):
        """応募可能かどうかを判定する（鉄の掟）"""
        count = self.get_monthly_application_count()
        if self.rank == 'iron':
            return count < 3
        elif self.rank == 'bronze':
            return count < 10
        # シルバー以上は無制限
        return True

# お気に入りエリア
class FavoriteArea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_areas')
    prefecture = models.CharField(max_length=20, choices=PREFECTURES, verbose_name="都道府県")
    city = models.CharField(max_length=50, blank=True, default='', verbose_name="市区町村")

    class Meta:
        verbose_name = "お気に入りエリア"
        verbose_name_plural = "お気に入りエリア一覧"

    def __str__(self):
        return f"{self.prefecture} {self.city}"

# シグナル：ユーザー作成時にプロフィールを自動生成
@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()