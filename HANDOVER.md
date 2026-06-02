# 建設マッチング（Elchristo）引き継ぎメモ

最終更新: 2026年6月

このドキュメントは、本プロジェクト（建設業向けマッチングアプリ）の開発・運用を引き継ぐための要点をまとめたものです。

---

## 1. 概要

- 建設業界向けのマッチングプラットフォーム（案件募集・応募・スカウト・契約成立までを仲介）。
- 本番環境: Render 上でホスティング（サービス名 `kensetsu-app-1`）。
- 公開ドメイン: `el-christo.jp` / `kensetsu-app-1.onrender.com`

---

## 2. 技術スタック

| 区分 | 内容 |
|------|------|
| 言語 | Python |
| フレームワーク | Django 6.0 |
| DB | PostgreSQL（`dj-database-url` で接続。ローカルは SQLite フォールバック） |
| アプリサーバー | Gunicorn |
| 静的ファイル | WhiteNoise |
| 画像ストレージ | Cloudinary（アバター等） / AWS S3（本人確認書類などの非公開ファイル: `PrivateS3Storage`） |
| 決済 | Stripe（`stripe==14.2.0`） |
| AI生成 | Anthropic Claude（`anthropic` SDK / モデル `claude-sonnet-4-20250514`） |
| メール | Gmail SMTP |
| ホスティング | Render |

### Djangoアプリ構成
- `accounts` — ユーザー・プロフィール・ランク・Eポイント・認証まわり
- `jobs` — 案件・応募・メッセージ・レビュー・スカウト・通知・お問い合わせ・ニュース
- `pages` — 静的ページ・ランディングページ・SEO記事

---

## 3. 環境変数（Render）

> ⚠️ **実際の値はこのドキュメントには記載しません。**
> 値はすべて **Render のダッシュボード（`kensetsu-app-1` → Environment）** で確認・設定してください。

### Stripe（**本番用に更新済み（2026年6月）**）
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

> 各プランの **Price ID（`STRIPE_PRICE_IDS`）は環境変数ではなく、コード内の `config/settings.py` にハードコードされています**。
> プラン価格を変更する際は `config/settings.py` の `STRIPE_PRICE_IDS`（silver / gold / platinum）を直接編集してください。
> こちらも 2026年6月に本番用 Price ID へ更新済み。

### AI（Anthropic）
- `ANTHROPIC_API_KEY` — **2026年6月追加済み**（AI自己紹介生成・AI案件説明文生成で使用）

### ストレージ
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### コア / Django
- `SECRET_KEY`
- `DEBUG`（本番は `False`）
- `DATABASE_URL`

### セキュリティ
- `RECAPTCHA_SECRET_KEY`

> ※ メール送信設定（Gmail SMTP）は現状 `config/settings.py` に直書きされています。将来的には環境変数化を推奨。

---

## 4. ランク体系（会員ランク）

`accounts/models.py` の `RANK_CHOICES` で定義。

| ランク | 月間応募上限 | 月間募集投稿上限 | 区分 |
|--------|------------|----------------|------|
| iron（デフォルト） | 3 | 0 | 無料 |
| bronze | 10 | 0 | 無料 |
| silver | 無制限 | 3 | 有料（Stripe） |
| gold | 無制限 | 無制限 | 有料（Stripe） |
| platinum | 無制限 | 無制限 | 有料（Stripe） |

- 有料ランク（silver / gold / platinum）は Stripe の月額サブスクで提供。Price ID は `config/settings.py` の `STRIPE_PRICE_IDS` を参照。
- Eポイント制度（`e_points` / `EPointHistory`）あり。
- 「創設メンバー」フラグ（`is_founding_member`）あり。

---

## 5. 実装済みの主な機能

- ユーザー登録・ログイン・パスワードリセット
- プロフィール（屋号、職種、所在地、経験年数、保有資格、インボイス番号 など）
- 本人確認（`id_card_image` を非公開S3に保存、`is_verified` フラグ・承認通知）
- 案件投稿（`Job`）／応募（`Application`）
- **応募〜契約の3段階フロー**（連絡先情報は契約成立後にのみ開示）
  - ステータス: 審査中 → 交渉中（チャット） → 契約成立 → 業務完了 ／ 辞退・見送り
- メッセージ機能（`Message`）／レビュー（`Review`）
- スカウト機能（`Scout`）／稼働ステータス（`WorkerAvailability`）
- 通知（`Notification`）・一斉配信（`Broadcast`）・ニュース（`News`）
- お問い合わせフォーム（メール通知、スパムキーワードフィルタ、ブロックメール機能）
- ブロック機能
- Stripe による有料ランクの決済・Webhook処理
- **AI自己紹介生成**（プロフィール編集画面、Claude）
- **AI案件説明文生成**（案件投稿、Claude）
- LINE公式アカウントのQRコード（ランディングページ）
- SEO記事ページ（職人不足2030、外注コスト削減、一人親方の安定 など）

---

## 6. 残課題・今後の改善候補

- [ ] メール送信設定（Gmail SMTP、`EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`）が `settings.py` に直書き → 環境変数化を推奨
- [ ] `STRIPE_PRICE_IDS` がコードにハードコード → 必要なら環境変数化を検討
- [ ] `config/settings.py` 内に開発時メモ・直書きの残り（`★後で変更` コメント等）の整理
- [ ] テストコードの整備

---

## 7. デプロイ・運用メモ

- Render に push すると自動デプロイ（`gunicorn` 起動）。
- 静的ファイルは WhiteNoise 配信。
- 本番 DB は Render の PostgreSQL（`DATABASE_URL`）。
- 環境変数を変更したら Render 側で再デプロイが必要。
- Stripe の本番/テスト切り替えは、Render の環境変数（`STRIPE_*`）と `settings.py` の `STRIPE_PRICE_IDS` の両方が本番用になっているか必ず確認すること。
