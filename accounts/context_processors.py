def rank_downgrade_check(request):
    """
    ログイン中ユーザーの無料ランク期限を「アクセスのたびに」チェックし、
    期限切れなら Profile.check_and_downgrade_rank() で自動的に降格させる。

    Render無料プラン等でcron/バッチが使えない環境でも確実に動くように、
    リクエストの副作用としてチェックを走らせるのが目的。
    テンプレートへ渡す値は無いので常に空dictを返す。
    """
    try:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            profile = getattr(user, "profile", None)
            if profile is not None:
                # 戻り値は使わない（副作用で降格させるのが目的）
                profile.check_and_downgrade_rank()
    except Exception:
        # 何が起きてもページ表示自体は止めない（握りつぶす）
        pass
    return {}
