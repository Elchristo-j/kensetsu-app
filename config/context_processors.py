def app_detection(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # iOSアプリ、または Androidアプリ からのアクセスなら「True」にする
    # （HTML側は is_ios_app のままで動くようにする裏技です）
    is_ios_app = ('elchristo-ios-app' in user_agent) or ('elchristo-android-app' in user_agent)
    
    return {
        'is_ios_app': is_ios_app,
    }