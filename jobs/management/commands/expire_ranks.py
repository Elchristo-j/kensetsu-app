from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile

# === 確定ルール（変更しないこと） =========================================
# 降格対象とするランク。無料ランクアップで付与されうるのは gold だが、
# 将来 silver 付与に変えた場合も拾えるよう課金ランク3種を対象にする。
PAID_RANKS = ['silver', 'gold', 'platinum']
# 参考表示のみ（降格対象にはしない）ランク
ALREADY_DOWNGRADED_RANKS = ['bronze', 'iron']
# ==========================================================================
#
# 【重要】判定ロジックはこのコマンドに書かない。
# 降格の正本は Profile.check_and_downgrade_rank() ただ1つ。
# ここは「期限切れの候補を集めて、そのメソッドを呼ぶ」だけに徹する。
#
# 【重要】ログにPII（メールアドレス・氏名・電話番号）を出さないこと。
# Renderのログは平文で残るため、出力してよいのは Profile.id と件数のみ。


class Command(BaseCommand):
    help = '無料ランクの有効期限が切れたユーザーを check_and_downgrade_rank() で降格させる'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際には降格させず、対象だけを表示する',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        # 降格対象：期限が設定済み かつ 期限切れ かつ 現ランクが課金ランク
        candidates = list(
            Profile.objects.filter(
                rank_expires_at__isnull=False,
                rank_expires_at__lte=now,
                rank__in=PAID_RANKS,
            ).order_by('id')
        )
        total = len(candidates)

        # 参考値：期限は残っているが、ランクは既に bronze/iron のレコード。
        # check_and_downgrade_rank() はこの場合 rank_expires_at をクリアせず
        # False を返すだけなので、データとしては残り続ける。降格対象にはしない。
        stale_count = Profile.objects.filter(
            rank_expires_at__isnull=False,
            rank__in=ALREADY_DOWNGRADED_RANKS,
        ).count()

        downgraded = 0
        skipped = 0
        failed = 0

        for profile in candidates:
            if dry_run:
                # DBは一切変更しない。出力はIDのみ（PIIを出さない）。
                self.stdout.write(f"  [降格対象] profile_id={profile.id}")
                downgraded += 1
                continue

            # 1件の失敗で全体を止めない
            try:
                if profile.check_and_downgrade_rank():
                    downgraded += 1
                else:
                    # 想定外（絞り込み条件と食い違った場合）。件数だけ記録する。
                    skipped += 1
            except Exception:
                failed += 1
                self.stdout.write(self.style.ERROR(
                    f"  [失敗] profile_id={profile.id}"
                ))

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}expire_ranks 完了 | "
            f"降格:{downgraded} / 対象外スキップ:{skipped} / 失敗:{failed} / "
            f"候補総数:{total}"
        ))
        self.stdout.write(
            f"{prefix}[参考] 期限が残っているが既に bronze/iron のレコード:{stale_count}件"
            f"（降格対象外・表示のみ）"
        )
