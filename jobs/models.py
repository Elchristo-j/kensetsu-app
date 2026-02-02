from django.db import models
from django.contrib.auth.models import User
from accounts.models import PREFECTURES
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# 業種・職種のリスト定義
JOB_CATEGORIES = [
    ('general', '多能工・手元'),
    ('carpenter', '大工・造作'),
    ('electric', '電気・通信'),
    ('plumbing', '設備・水道'),
    ('interior', '内装・クロス・床'),
    ('exterior', '外装・塗装・防水'),
    ('scaffold', '足場・鳶・土工'),
    ('hvac', '空調・ダクト'),
    ('cleaning', 'クリーニング・雑工'),
    ('other', 'その他'),
]

class Job(models.Model):
    title = models.CharField(max_length=100, verbose_name="仕事のタイトル")
    
    # 業種（カテゴリ）フィールド
    category = models.CharField(
        max_length=50, 
        choices=JOB_CATEGORIES, 
        default='general', 
        verbose_name='業種・職種'
    )

    work_date = models.CharField(max_length=100, blank=True, verbose_name="勤務日・期間")
    description = models.TextField(verbose_name="作業内容の詳細")
    working_hours = models.CharField(max_length=100, blank=True, verbose_name="勤務時間帯")
    break_time = models.CharField(max_length=100, blank=True, verbose_name="休憩時間")
    qualifications = models.TextField(blank=True, verbose_name="応募資格・必要な道具など")
    notes = models.TextField(blank=True, verbose_name="備考（男女・年齢不問、特記事項など）")

    price = models.IntegerField(verbose_name="金額")
    UNIT_CHOICES = [('日', '日給'), ('時', '時給'), ('件', '1件あたり')]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='日', verbose_name="単位")
    
    prefecture = models.CharField(max_length=10, choices=PREFECTURES, default='徳島県', verbose_name="都道府県")
    city = models.CharField(max_length=50, blank=True, default='', verbose_name="市区町村")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="募集期限")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_closed = models.BooleanField(default=False, verbose_name="募集終了")
    headcount = models.IntegerField(default=1, verbose_name="募集人数")

    def __str__(self):
        return self.title

    @property
    def is_new(self):
        """投稿から48時間以内ならTrue"""
        return self.created_at >= timezone.now() - timedelta(hours=48)

    @property
    def accepted_count(self):
        """採用済み（status='accepted'）の人数を返す"""
        return self.applications.filter(status='accepted').count()
    
    @property
    def recruitment_status(self):
        """表示用：採用人数 / 募集人数"""
        limit = getattr(self, 'headcount', 1) 
        return f"{self.accepted_count} / {limit}"


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('applied', '選考中'),
        ('accepted', '採用'),
        ('rejected', '不採用'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"


class Message(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message by {self.sender.username}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.username}"


class Review(models.Model):
    # どちら向きの評価かを判別
    REVIEW_TYPE_CHOICES = (
        ('employer_to_worker', '発注者からワーカーへ'),
        ('worker_to_employer', 'ワーカーから発注者へ'),
    )

    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='reviews', verbose_name='対象案件')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_reviews', verbose_name='評価者')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reviews', verbose_name='被評価者')
    review_type = models.CharField('評価タイプ', max_length=20, choices=REVIEW_TYPE_CHOICES)
    
    # --- 発注者 → ワーカーへの評価項目 (0-10) ---
    ability = models.IntegerField('能力', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    cooperation = models.IntegerField('協調性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    diligence = models.IntegerField('勤勉性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    humanity = models.IntegerField('人間性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    
    # 有用性は「金額」で入力され、裏側で0-10に変換されて保存される想定
    utility_amount = models.IntegerField('有用性(金額評価)', null=True, blank=True, help_text='日当換算での価値')
    utility_score = models.IntegerField('有用性スコア', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)

    # --- ワーカー → 発注者への評価項目 (0-10) ---
    working_hours = models.IntegerField('作業時間', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    reward = models.IntegerField('報酬', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    job_content = models.IntegerField('仕事内容', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    preparation = models.IntegerField('段取り', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    credibility = models.IntegerField('信用性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)

    comment = models.TextField('コメント', blank=True)
    created_at = models.DateTimeField('評価日時', auto_now_add=True)

    def save(self, *args, **kwargs):
        # 有用性スコアの自動計算ロジック（発注者→ワーカーの場合）
        if self.review_type == 'employer_to_worker' and self.utility_amount is not None:
            self.utility_score = self.calculate_utility_score(self.utility_amount)
        super().save(*args, **kwargs)

    @staticmethod
    def calculate_utility_score(amount):
        """
        金額テーブルに基づいて有用性スコア(0-10)を算出
        ⓪-3,000以下, ①-4,000〜6,000 ... ⑩-31,000以上
        """
        if amount <= 3499: return 0  # 3000以下（四捨五入考慮）
        if amount <= 6499: return 1  # 4000-6000
        if amount <= 9499: return 2  # 7000-9000
        if amount <= 12499: return 3 # 10000-12000
        if amount <= 15499: return 4 # 13000-15000
        if amount <= 18499: return 5 # 16000-18000
        if amount <= 21499: return 6 # 19000-21000
        if amount <= 24499: return 7 # 22000-24000
        if amount <= 27499: return 8 # 25000-27000
        if amount <= 30499: return 9 # 28000-30000
        return 10                    # 31000以上

    def __str__(self):
        return f"{self.reviewer} -> {self.reviewee} ({self.job})"