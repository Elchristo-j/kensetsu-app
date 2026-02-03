from django.contrib import admin
from .models import Job, Application, Message, Notification, Review

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