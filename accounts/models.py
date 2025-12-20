from django.db import models
from django.contrib.auth.models import User

# ユーザー情報の拡張ポケット（プロフィール）
class Profile(models.Model):
    # どのユーザーのプロフィールか（1対1の関係）
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 顔写真・ロゴ画像（imagesフォルダの中に profile_images というフォルダを作って保存する）
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    # 対応エリア（例：大阪市、福岡県全域など）
    location = models.CharField(max_length=100, blank=True, null=True)
    
    # 自己紹介・実績のアピール
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}のプロフィール"