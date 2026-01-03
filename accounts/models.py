from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    ユーザーの属性を拡張するプロフィールモデル。
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name="ユーザー"
    )
    
    # 以前のご要望に合わせて、verbose_name を「拠点」に変更しました
    location = models.CharField(
        max_length=100, 
        blank=True, 
        default='', 
        verbose_name="拠点"
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

    # --- ここが新機能：未読通知があるかチェックする機能 ---
    @property
    def has_unread_notifications(self):
        """
        現在のユーザーに「未読(is_read=False)」の通知が
        1つ以上ある場合は True を返します。
        """
        return self.user.notifications.filter(is_read=False).exists()


# --- シグナル設定：ユーザー作成時にプロフィールを自動生成（これは絶対に残すべき重要コードです） ---

@receiver(post_save, sender=User)
def handle_user_profile_sync(sender, instance, created, **kwargs):
    """
    ユーザーの生成・更新に合わせてプロフィールを同期します。
    """
    if created:
        # ユーザー新規作成時にプロフィールを自動で作成します
        Profile.objects.create(user=instance)
    else:
        # ユーザー更新時にプロフィールを保存します
        if hasattr(instance, 'profile'):
            instance.profile.save()