from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    ユーザーの属性を拡張するプロフィールモデル。
    Userモデルと1対1で紐付き、職人としての「顔」を定義します。
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="ユーザー"
    )
    
    # 文字列フィールドにおいて、DjangoではNULLと空文字の混在を避けるため
    # blank=True のみを指定するのがベストプラクティスです。
    location = models.CharField(
        max_length=100, 
        blank=True, 
        default='', 
        verbose_name="活動エリア"
    )
    
    description = models.TextField(
        blank=True, 
        default='', 
        verbose_name="自己紹介・実績"
    )
    
    image = models.ImageField(
        upload_to='profile_images/', 
        blank=True, 
        null=True, 
        verbose_name="アイコン画像"
    )

    class Meta:
        verbose_name = "プロフィール"
        verbose_name_plural = "プロフィール一覧"

    def __str__(self):
        return f"{self.user.username} のプロフィール"


# --- シグナル設定：ユーザー作成時にプロフィールを自動生成 ---

@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    """
    ユーザーの生成・更新に合わせてプロフィールを同期します。
    createとsaveを一つの関数にまとめることで、保守性を高めています。
    """
    if created:
        # ユーザー新規作成時
        Profile.objects.create(user=instance)
    else:
        # ユーザー更新時（プロフィールが存在することを確認してから保存）
        if hasattr(instance, 'profile'):
            instance.profile.save()