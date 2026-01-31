from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def custom_timesince(value):
    """
    作成日時からの経過時間をカスタム表示するフィルタ
    - 24時間以内: 「〇〇時間前」
    - 24〜48時間: 「1日と〇〇時間前」
    - 48時間以降: 「〇〇日前」
    """
    if not value:
        return ""

    now = timezone.now()
    diff = now - value

    # 経過秒数
    seconds = diff.total_seconds()
    
    # 24時間（86400秒）未満
    if seconds < 86400:
        hours = int(seconds // 3600)
        # 1時間未満の場合
        if hours == 0:
            minutes = int(seconds // 60)
            return f"{minutes}分前"
        return f"{hours}時間前"

    # 48時間（172800秒）未満
    elif seconds < 172800:
        hours = int((seconds - 86400) // 3600)
        return f"1日と{hours}時間前"

    # それ以降
    else:
        return f"{diff.days}日前"