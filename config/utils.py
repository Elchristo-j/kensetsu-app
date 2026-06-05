from functools import wraps
from django.shortcuts import redirect

# アプリ（iOS/Android）判定に使うUA識別子。
# ※ context_processors.app_detection と必ず同じ文字列を使うこと。
#   新しい判定基準を勝手に増やさない。
APP_USER_AGENT_KEYWORDS = ('elchristo-ios-app', 'elchristo-android-app')


def is_app_request(request):
    """
    リクエストが自社アプリ（iOS/Android）からのものかを判定する。
    判定は User-Agent に APP_USER_AGENT_KEYWORDS が含まれるかどうかのみ。
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    return any(keyword in user_agent for keyword in APP_USER_AGENT_KEYWORDS)


def block_in_app(view_func):
    """
    アプリ（iOS/Android）からのアクセス時は home へリダイレクトするデコレータ。
    課金UI／課金開始ビューに付けて、直接URLアクセスでも課金導線を見せない。
    （Apple審査要件：直接URLでも課金UIが見えないこと）
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if is_app_request(request):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped
