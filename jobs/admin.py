from django.contrib import admin
from .models import Job, Application, Message, Notification, Review, Contact, Broadcast, News, Scout# ← 最後にScoutを追加しました！

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_closed')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('job', 'reviewer', 'reviewee', 'review_type', 'utility_score')
    list_filter = ('review_type',)

admin.site.register(Job, JobAdmin)
admin.site.register(Application)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(Review, ReviewAdmin) # ← これで評価データが見れるようになります
admin.site.register(Broadcast)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at') # 一覧に出す項目
    list_filter = ('created_at',) # 日付で絞り込み
    search_fields = ('name', 'email', 'subject', 'message') # 検索機能
    readonly_fields = ('created_at',) # 日付は書き換え不可に

# ▼▼ 今回追加：お知らせ（News）を管理画面に登録 ▼▼
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'created_at') # 一覧画面で見える項目
    list_filter = ('category', 'is_published') # 横の絞り込みメニュー
    search_fields = ('title', 'content')  # 検索窓の対象
    
@admin.register(Scout)
class ScoutAdmin(admin.ModelAdmin):
    list_display = ('employer', 'worker', 'target_job', 'created_at') # 一覧に表示する項目
    list_filter = ('created_at',)  # 日付で絞り込めるようにする
       