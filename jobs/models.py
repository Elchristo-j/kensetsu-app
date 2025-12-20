from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    # ★追加：募集終了フラグ（Trueなら募集終了）
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    # ★追加：ステータス（applied=応募中, accepted=採用, rejected=不採用）
    status = models.CharField(max_length=20, default='applied')

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"

class Message(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"