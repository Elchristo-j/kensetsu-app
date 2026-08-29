"""
未有効化アカウントの削除コマンド。

仮登録（is_active=False）のまま一定日数を過ぎたアカウントを削除する。
2026年8月25日に、CAPTCHA解読サービス経由と思われるボットが仮登録だけ行い
本登録せずに放置するケースを確認したため追加した。
放置するとアカウント数の実態が分からなくなり、
「新規登録の推移を週1で観察する」運用の判断材料が汚れる。

使い方:
    python manage.py cleanup_unverified_users --dry-run   # 確認のみ（削除しない）
    python manage.py cleanup_unverified_users             # 実削除
    python manage.py cleanup_unverified_users --days 14   # 猶予日数を変更
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# 仮登録から削除までの猶予日数。
# メールが迷惑メールフォルダに入り、数日後に気づいて本登録する人を潰さないため
# 短くしすぎないこと。
DEFAULT_GRACE_DAYS = 7


class Command(BaseCommand):
    help = '仮登録（is_active=False）のまま一定日数を過ぎたアカウントを削除します。'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='削除せず、対象となるアカウントの一覧のみ表示します。',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=DEFAULT_GRACE_DAYS,
            help=f'仮登録から削除までの猶予日数（既定: {DEFAULT_GRACE_DAYS}日）。',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']

        if days < 3:
            self.stdout.write(self.style.ERROR(
                f'猶予日数が短すぎます（{days}日）。3日以上を指定してください。'
            ))
            return

        User = get_user_model()
        cutoff = timezone.now() - timedelta(days=days)

        # is_staff / is_superuser は絶対に対象外。
        # 運営アカウントを誤って消すと復旧できないため、二重に除外する。
        #
        # last_login__isnull=True も必須の条件。
        # accounts/views.py の account_delete（退会処理）も is_active=False を
        # 立てるため、is_active だけで絞ると退会ユーザーまで巻き込んで
        # 削除してしまう（案件・応募・レビュー等がカスケードで消える）。
        # 退会するにはログインが必要なので last_login は必ず入っている。
        # 一方、仮登録のまま放置されたアカウントは一度もログインしていない。
        # この差で「仮登録の残骸」だけを安全に絞り込む。
        targets = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff,
            last_login__isnull=True,
        ).exclude(
            is_staff=True,
        ).exclude(
            is_superuser=True,
        ).order_by('date_joined')

        count = targets.count()

        self.stdout.write(
            f'基準日時: {cutoff:%Y-%m-%d %H:%M} （{days}日以上前に仮登録され、未有効化のまま）'
        )

        if count == 0:
            self.stdout.write(self.style.SUCCESS('対象となるアカウントはありません。'))
            return

        self.stdout.write(f'対象: {count}件')
        for user in targets:
            self.stdout.write(
                f'  - id={user.pk} / {user.username} / {user.email} '
                f'/ 登録日時 {user.date_joined:%Y-%m-%d %H:%M}'
            )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n--dry-run のため削除していません。'
                '\n実行するには --dry-run を外して再実行してください。'
            ))
            return

        deleted, _ = targets.delete()
        self.stdout.write(self.style.SUCCESS(
            f'\n{count}件のアカウントを削除しました（関連レコード含め {deleted} 行）。'
        ))
