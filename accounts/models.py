from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # 以前作ったフィールドがあればそのまま、今回は以下を追加・整理します
    description = models.TextField(blank=True, null=True, verbose_name="自己紹介")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="活動エリア")
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name="アイコン画像")

    def __str__(self):
        return self.user.username

# ユーザー作成時に自動でプロフィールも作る機能
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()