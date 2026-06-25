from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from jobs.models import Job, EPointHistory

# === 確定ルール（変更しないこと） =========================================
# この日以降に投稿された案件のみ評価対象（過去案件への一斉付与を防ぐ）
CUTOFF_DATE = date(2026, 6, 26)
# 投稿から何日後に付与するか
DAYS_THRESHOLD = 7
# 付与ポイント
POINTS = 1
# 8割条件：下記10項目のうち、何項目以上の記入で付与するか
REQUIRED_FILLED_COUNT = 8
# 8割判定の母数（既定値で自動的に埋まる4項目は除外済み）
FILL_CHECK_FIELDS = [
    'title', 'work_date', 'description', 'working_hours', 'break_time',
    'qualifications', 'price', 'city', 'deadline', 'notes',
]
# ==========================================================================


class Command(BaseCommand):
    help = '投稿から7日経過し、本人確認済み・8割記入の案件にEポイント(+1)を付与する'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際には付与せず、対象だけを表示する',
        )

    def count_filled(self, job):
        """10項目のうち、非空の項目数を数える"""
        count = 0
        for field_name in FILL_CHECK_FIELDS:
            value = getattr(job, field_name, None)
            if value is None:
                continue
            if isinstance(value, str):
                if value.strip():
                    count += 1
            else:
                # price(int) / deadline(datetime) は None でなければ記入済み
                count += 1
        return count

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        seven_days_ago = now - timedelta(days=DAYS_THRESHOLD)

        # カットオフ日以降に投稿され、かつ投稿から7日以上経過した案件
        candidates = list(
            Job.objects.filter(
                created_at__date__gte=CUTOFF_DATE,
                created_at__lte=seven_days_ago,
            ).select_related('created_by')
        )
        total = len(candidates)

        granted = 0
        skipped_already = 0
        skipped_unverified = 0
        skipped_fill = 0

        for job in candidates:
            # 二重付与防止：既にこの案件で job_posted 履歴があるか
            already = EPointHistory.objects.filter(
                related_job=job, action_type='job_posted'
            ).exists()
            if already:
                skipped_already += 1
                continue

            # 本人確認：判定時点で投稿者が is_verified=True か
            try:
                profile = job.created_by.profile
            except (ObjectDoesNotExist, AttributeError):
                profile = None
            if profile is None or not profile.is_verified:
                skipped_unverified += 1
                continue

            # 8割条件：10項目中8項目以上が非空か
            if self.count_filled(job) < REQUIRED_FILLED_COUNT:
                skipped_fill += 1
                continue

            # ここまで通れば付与対象
            if dry_run:
                self.stdout.write(
                    f"  [付与対象] job_id={job.id} title={job.title}"
                )
            else:
                EPointHistory.objects.create(
                    user=job.created_by,
                    action_type='job_posted',
                    points=POINTS,
                    description=f"案件「{job.title}」の投稿（7日継続）",
                    related_job=job,
                    related_application=None,
                )
            granted += 1

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}grant_post_points 完了 | "
            f"付与:{granted} / 既付与スキップ:{skipped_already} / "
            f"未確認スキップ:{skipped_unverified} / 記入不足スキップ:{skipped_fill} / "
            f"候補総数:{total}"
        ))
