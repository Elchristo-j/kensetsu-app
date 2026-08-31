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


# ---------------------------------------------------------------------------
# 海外フリーメール／使い捨てメールのドメイン拒否リスト
# ---------------------------------------------------------------------------
# 目的：CAPTCHA解読サービスを使うボットの登録を、メールドメインで足切りする。
#
# ⚠️ 追加してよいのは「東四国の建設業者がまず使わないドメイン」だけ。
#    日本の主要プロバイダ（gmail.com / yahoo.co.jp / icloud.com / outlook.com /
#    hotmail.co.jp / docomo.ne.jp / ezweb.ne.jp / softbank.ne.jp / ocn.ne.jp /
#    nifty.com / biglobe.ne.jp / so-net.ne.jp 等）は絶対に入れないこと。
#    ここに1つ入れ間違えると、本物の登録者が「何も起きない」まま消える。
BLOCKED_EMAIL_DOMAINS = frozenset({
    # --- 海外フリーメール（ボットの定番） ---
    'gmx.com', 'gmx.us', 'gmx.net', 'gmx.de', 'gmx.at', 'gmx.ch',
    'gmx.fr', 'gmx.co.uk',
    'mail.com', 'email.com', 'usa.com', 'consultant.com', 'post.com',
    'mail.ru', 'bk.ru', 'list.ru', 'inbox.ru', 'internet.ru',
    'yandex.ru', 'yandex.com', 'ya.ru',
    'rambler.ru',
    'seznam.cz',
    'wp.pl', 'o2.pl', 'onet.pl', 'interia.pl',
    'abv.bg',
    'libero.it', 'virgilio.it', 'tiscali.it',
    'web.de', 't-online.de', 'freenet.de',
    'laposte.net',

    # --- 使い捨てメール ---
    'mailinator.com', 'guerrillamail.com', 'sharklasers.com', 'grr.la',
    '10minutemail.com', 'temp-mail.org', 'tempmail.com', 'yopmail.com',
    'dispostable.com', 'trashmail.com', 'maildrop.cc', 'getnada.com',
    'throwawaymail.com', 'mohmal.com', 'emailondeck.com', 'fakemail.net',
    'mytemp.email', 'moakt.com', 'tempr.email', 'spam4.me',
})


def is_blocked_email_domain(email):
    """
    メールアドレスのドメインが拒否リストに該当するかを判定する。
    サブドメイン（例：mail.gmx.us）も同じ扱いにする。
    判定できない入力（空・@なし）は False を返し、通常のバリデーションに任せる。
    """
    if not email or '@' not in email:
        return False
    domain = email.rsplit('@', 1)[1].strip().lower().rstrip('.')
    if not domain:
        return False
    if domain in BLOCKED_EMAIL_DOMAINS:
        return True
    return any(domain.endswith('.' + blocked) for blocked in BLOCKED_EMAIL_DOMAINS)
