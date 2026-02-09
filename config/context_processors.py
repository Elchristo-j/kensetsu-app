# ファイル名: context_processors.py

def app_detection(request):
    """
    アクセス元のUser-Agentを見て、iOSアプリかどうかを判定する関数
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # ★ここが合言葉です。アプリ側で設定するUserAgent名と合わせます。
    # 特殊文字（'）は避けて、シンプルな英数字にするのが無難です。
    is_ios_app = 'elchristo-ios-app' in user_agent
    
    # テンプレート（HTML）内で {{ is_ios_app }} と書けば True/False が返るようになります
    return {
        'is_ios_app': is_ios_app
    }