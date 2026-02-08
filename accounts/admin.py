from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, FavoriteArea, Block, Report

# プロフィール単体でも管理できるように登録
admin.site.register(Profile)

# ▼▼▼ 通報リストの設定 ▼▼▼
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'target', 'reason', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('reason', 'reporter__username', 'target__username')

# ▼▼▼ ブロックリストの設定 ▼▼▼
@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')

# ユーザー編集画面の中にプロフィールを埋め込む設定
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'プロフィール情報'
    fk_name = 'user'

# 新しいユーザー管理画面の定義
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    
    # ★ここに 'get_founding' を追加しました！
    list_display = ('username', 'email', 'get_rank', 'get_founding', 'is_staff')
    
    # ランクを表示する関数
    def get_rank(self, obj):
        # 万が一プロフィールがない場合のエラー回避
        if hasattr(obj, 'profile'):
            return obj.profile.get_rank_display()
        return '-'
    get_rank.short_description = '会員ランク'

    # ★創設メンバーかどうかを表示する関数
    def get_founding(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.is_founding_member
        return False
    get_founding.boolean = True # これで True/False がアイコン（✅/❌）になります
    get_founding.short_description = '創設メンバー'

# 元々のUser設定を解除して、新しい設定で再登録
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(FavoriteArea)