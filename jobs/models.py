from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Job(models.Model):
    # ★追加：単位の選択肢
    UNIT_CHOICES = [
        ('日', '日給 (/日)'),
        ('時', '時給 (/時間)'),
        ('月', '月給 (/月)'),
        ('一式', '一式 (請負)'),
    ]

    title = models.CharField(max_length=100, verbose_name="仕事のタイトル")
    description = models.TextField(verbose_name="仕事の詳細")
    
    # ★変更：金額と単位
    price = models.IntegerField(verbose_name="金額")
    unit = models.CharField(
        max_length=10, 
        choices=UNIT_CHOICES, 
        default='日', 
        verbose_name="単位"
    )

    # ★追加：募集人数
    headcount = models.IntegerField(default=1, verbose_name="募集人数")

    # ★追加：募集期限（カレンダー入力用）
    deadline = models.DateField(null=True, blank=True, verbose_name="募集期限")

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    # 募集終了フラグ
    is_closed = models.BooleanField(default=False, verbose_name="募集終了")

    def __str__(self):
        return self.title

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    # ステータス（そのまま維持）
    status = models.CharField(max_length=20, default='applied')

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"

# チャット機能（そのまま維持）
class Message(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"