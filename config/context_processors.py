def app_detection(request):
    """
    アクセス元のUser-Agentを見て、iOSアプリかどうかを判定する関数
    
    【仕組み】
    iOSアプリ側（ViewController.swift）で設定した合言葉
    "Elchristo-iOS-App" が含まれているかをチェックします。
    """
    
    # User-Agentを取得し、すべて「小文字」に変換して比較しやすくする
    # （これなら Swift側で "Elchristo..." でも "elchristo..." でもヒットします）
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # ★合言葉のチェック★
    # Swift側で設定する "Elchristo-iOS-App" が含まれているか？
    is_ios_app = 'elchristo-ios-app' in user_agent
    
    # デバッグ用（本番では消しても良いですが、ログで確認できると便利です）
    # print(f"DEBUG: User-Agent={user_agent}, is_ios_app={is_ios_app}")

    # テンプレート（HTML）内で {{ is_ios_app }} と書けば True/False が返るようになります
    return {
        'is_ios_app': is_ios_app
    }