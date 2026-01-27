from django.db import models
from django.contrib.auth.models import User
from accounts.models import PREFECTURES

class Job(models.Model):
    title = models.CharField(max_length=100, verbose_name="仕事のタイトル")
    
    # 追加した項目：勤務日・期間
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

    # ▼▼▼ 追加箇所ここから ▼▼▼
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
        # headcountフィールドがない場合は暫定で '∞' や '-' にしてください
        # ここでは headcount がある前提、なければ仮に 1 とします
        limit = getattr(self, 'headcount', 1) 
        return f"{self.accepted_count} / {limit}"
    # ▲▲▲ 追加箇所ここまで ▲▲▲

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
    is_read = models.BooleanField(default=False)  # ←これを追加

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