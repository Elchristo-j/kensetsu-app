from django.db import models
from django.contrib.auth.models import User
from accounts.models import PREFECTURES
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# ★職種リストを修正しました
# ジャンルごとにコメントで区切っています
JOB_CATEGORIES = [
    # --- 多能工 ---
    ('general', '多能工・手元'),

    # --- 建築・躯体 ---
    ('carpenter', '大工（造作・建具）'),
    ('formwork', '型枠大工・鉄筋工'),
    ('plasterer', '左官・タイル'),       # 追加
    ('sheet_metal', '板金・外壁・屋根'), # 追加
    ('lgs', '軽天・ボード貼り'),         # 追加

    # --- 設備 ---
    ('electric', '電気工・通信・消防'),
    ('plumbing', '配管工・設備・水道'),
    ('hvac', '空調・ダクト'),

    # --- 内装・仕上げ ---
    ('interior', '内装（クロス・床）'),
    ('painting', '塗装・防水'),
    ('scaffold', '鳶・足場'),
    ('cleaning', '美装'),

    # --- 管理・その他 ---
    ('supervisor', '現場監督・現場代理人'), # 追加
    ('other', 'その他'),
]

class Job(models.Model):
    title = models.CharField(max_length=100, verbose_name="仕事のタイトル")
    category = models.CharField(max_length=50, choices=JOB_CATEGORIES, default='general', verbose_name='業種・職種')
    work_date = models.CharField(max_length=100, blank=True, verbose_name="勤務日・期間")
    description = models.TextField(verbose_name="作業内容の詳細")
    working_hours = models.CharField(max_length=100, blank=True, verbose_name="勤務時間帯")
    break_time = models.CharField(max_length=100, blank=True, verbose_name="休憩時間")
    qualifications = models.TextField(blank=True, verbose_name="応募資格・必要な道具など")
    notes = models.TextField(blank=True, verbose_name="備考")
    price = models.IntegerField(verbose_name="金額")
    UNIT_CHOICES = [('日', '日給'), ('時', '時給'), ('件', '1件あたり')]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='日', verbose_name="単位")
    prefecture = models.CharField(max_length=10, choices=PREFECTURES, default='徳島県', verbose_name="都道府県")
    city = models.CharField(max_length=50, blank=True, default='', verbose_name="市区町村")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="募集期限")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    is_closed = models.BooleanField(default=False, verbose_name="募集終了")
    headcount = models.IntegerField(default=1, verbose_name="募集人数")

    def __str__(self):
        return self.title

    @property
    def is_new(self):
        return self.created_at >= timezone.now() - timedelta(hours=48)

    @property
    def accepted_count(self):
        # 契約成立・業務完了になった人数をカウントする
        return self.applications.filter(status__in=['contracted', 'completed']).count()
    
    @property
    def recruitment_status(self):
        limit = getattr(self, 'headcount', 1) 
        return f"{self.accepted_count} / {limit}"

    # ▼▼▼ 修正：ここが正しい「残り人数の計算」の場所です ▼▼▼
    @property
    def remaining_headcount(self):
        # 「契約成立」または「業務完了」になった人数だけを引く（交渉中はまだ引かない）
        filled_count = self.applications.filter(status__in=['contracted', 'completed']).count()
        return max(0, self.headcount - filled_count)
    # ▲▲▲ 修正ここまで ▲▲▲

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = (
        ('pending', '審査中'),
        ('accepted', '交渉中（チャットへ）'),  # ←「採用」から変更
        ('contracted', '契約成立'),
        ('completed', '業務完了'),
        ('canceled', '辞退'),
        ('rejected', '見送り（また今度お願いします）'),  # ←「不採用」から変更
    )
    # デフォルトのステータスを pending に修正（これがないと応募時にエラーになる可能性があります）
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"


class Message(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    # ★重要：エラー回避のため image フィールドを削除しました


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    REVIEW_TYPE_CHOICES = (
        ('employer_to_worker', '発注者からワーカーへ'),
        ('worker_to_employer', 'ワーカーから発注者へ'),
    )

    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='reviews', verbose_name='対象案件')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_reviews', verbose_name='評価者')
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_reviews', verbose_name='被評価者')
    review_type = models.CharField('評価タイプ', max_length=20, choices=REVIEW_TYPE_CHOICES)
    
    ability = models.IntegerField('能力', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    cooperation = models.IntegerField('協調性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    diligence = models.IntegerField('勤勉性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    humanity = models.IntegerField('人間性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    utility_amount = models.IntegerField('有用性(金額)', null=True, blank=True)
    utility_score = models.IntegerField('有用性スコア', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)

    working_hours = models.IntegerField('作業時間', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    reward = models.IntegerField('報酬', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    job_content = models.IntegerField('仕事内容', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    preparation = models.IntegerField('段取り', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    credibility = models.IntegerField('信用性', validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)

    comment = models.TextField('コメント', blank=True)
    created_at = models.DateTimeField('評価日時', auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.review_type == 'employer_to_worker' and self.utility_amount is not None:
            self.utility_score = self.calculate_utility_score(self.utility_amount)
        super().save(*args, **kwargs)

    @staticmethod
    def calculate_utility_score(amount):
        if amount <= 3499: return 0
        if amount <= 6499: return 1
        if amount <= 9499: return 2
        if amount <= 12499: return 3
        if amount <= 15499: return 4
        if amount <= 18499: return 5
        if amount <= 21499: return 6
        if amount <= 24499: return 7
        if amount <= 27499: return 8
        if amount <= 30499: return 9
        return 10

    def __str__(self):
        return f"{self.reviewer} -> {self.reviewee} ({self.job})"
    
class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("お名前", max_length=100)
    email = models.EmailField("メールアドレス")
    subject = models.CharField("件名", max_length=200)
    message = models.TextField("お問い合わせ内容")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject