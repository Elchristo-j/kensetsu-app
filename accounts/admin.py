from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, FavoriteArea

# ユーザー編集画面の中にプロフィール（ランクなど）を埋め込む設定
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'プロフィール情報'
    fk_name = 'user'

# 新しいユーザー管理画面の定義
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
    # 一覧画面でIDなどを確認しやすくする
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_rank')
    
    def get_rank(self, obj):
        return obj.profile.rank
    get_rank.short_description = '会員ランク'

# 元々のUser設定を解除して、新しい設定で再登録
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(FavoriteArea)