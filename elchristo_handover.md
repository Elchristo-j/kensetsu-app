# El'christo 建設マッチングアプリ 引き継ぎメモ

*最終更新：2026年6月*

---

## プロジェクト概要

- **サービス名**：建設マッチング El'christo（エルクリスト）  
- **URL**：[https://el-christo.jp](https://el-christo.jp)  
- **対象エリア**：東四国（徳島県・香川県）  
- **ターゲット**：発注者（元請け・現場監督）と受注者（職人・作業員）  
- **運営**：吉川（一人運営・建設業界25年以上のキャリアを持つ）  
- **開発経緯**：2025年末〜2026年初頭にGeminiと共同で開発・2026年3月にiOS/Android両ストアで正式リリース。その後ClaudeにAIを切り替えて運用継続中。

---

## 技術スタック

| 項目 | 内容 |
| :---- | :---- |
| バックエンド | Django 6.0 / Python 3.13 |
| ホスティング | Render（Free プラン） |
| DB | PostgreSQL（Render） |
| ストレージ | Cloudinary（画像）/ AWS S3（本人確認書類） |
| 決済 | Stripe（本番モード・2026年6月に本番化完了） |
| ドメイン | お名前.com（el-christo.jp） |
| メール | [kma.elchristo@gmail.com](mailto:kma.elchristo@gmail.com)（送受信）/ [info@el-christo.jp](mailto:info@el-christo.jp)（受信のみ確認済） |
| バージョン管理 | GitHub（Elchristo-j/kensetsu-app） |
| AI | Anthropic Claude API（claude-sonnet-4-20250514） |

---

## ランク体系

| ランク | 条件 | 応募 | 募集投稿 | 月額 |
| :---- | :---- | :---- | :---- | :---- |
| iron | メール登録のみ | 月3回 | 不可 | 無料 |
| bronze | 本人確認済み | 月10回 | 不可 | 無料 |
| SILVER | サブスク | 無制限 | 月3回 | ¥550 |
| GOLD | サブスク | 無制限 | 無制限 | ¥2,200 |
| PLATINUM | サブスク | 無制限 | 無制限 | ¥5,500 |

---

## 現在の運営状況（2026年6月時点）

- **実質登録者数**：11名（全体18名のうち吉川本人・知人アカウント7つを除く）  
- **集客手段**：名刺型チラシによる口コミが現状のメイン  
- **CTR**：広告時1.69%（LP品質は良好）  
- **課題**：登録者が少ないためマッチングが成立しにくい「鶏と卵」問題

---

## 広告・マーケティング現状

### Meta広告（終了）

- キャンペーン名：El'christo\_発注者向け\_2026年3月  
- 期間：2026/03/21〜2026/04/04  
- 結果：消化¥6,908 / CTR 1.69% / LPV 117 / 登録0  
- 問題：広告コピーに「施工会社」という言葉を使ったことでターゲットとのミスマッチが発生

### Google検索広告（終了・停止中）

- キャンペーン名：El'christo\_発注者向け検索\_2026年5月  
- 期間：2026/04/08〜2026/05/17  
- 予算：¥700/日（合計¥30,000）  
- 結果：表示回数0・クリック0（検索ボリューム不足）

### メール営業（中止）

- 徳島県内建設業者60社へのメール営業を準備していたが、特定電子メール法（オプトイン原則）に抵触するグレーゾーンと判断し中止。

### 次の広告戦略（検討中）

- \*\*キーワード：「AI」\*\*を前面に打ち出す方針  
- 訴求コンセプト：「職人もAIの時代へ。登録3分、あとはAIにおまかせ。」  
- **タイミング**：建設業の閑散期（梅雨・台風時期の6〜7月、9月、4月）に合わせて打つのが効果的  
- **メッセージ方針**：「今は登録だけでいい。困った時に使えるように。」という低ハードル・将来保険の訴求

---

## LP（ランディングページ）

| ページ | URL | 対象 |
| :---- | :---- | :---- |
| 発注者向けLP | [https://el-christo.jp/lp/client/](https://el-christo.jp/lp/client/) | 元請け・現場監督 |
| 受注者向けLP | [https://el-christo.jp/lp/worker/](https://el-christo.jp/lp/worker/) | 職人・作業員 |

- Djangoの `pages` アプリで管理（`pages/templates/pages/`）  
- **キャンペーン訴求**：「新規登録限定・SILVER・GOLDプラン初月無料」（日付指定なし・常設訴求に変更済み）  
- **LINE QRコード**：両LPのCTAセクション下部に追加済み（2026年6月）

---

## SEOコラム記事（2026年6月追加）

集客の入り口として、検索流入を狙ったコラム記事を3本公開。全ページのフッター（`base.html`）からリンクを張りSEO効果を高めている。

| 記事 | URL | 対象 |
| :---- | :---- | :---- |
| 建設業の職人不足は2030年にどうなるか | `/column/worker-shortage-2030/` | 発注者 |
| 建設業の外注費を下げる3つの方法 | `/column/reduce-outsourcing-cost/` | 発注者 |
| 一人親方が仕事を安定させるために今できること | `/column/solo-worker-stability/` | 受注者 |

- 実装ファイル：`pages/templates/pages/article_*.html` / `pages/views.py`（TemplateView）/ `pages/urls.py`  
- デザイン：ゴールド（\#d4af37）× ブラック（\#111111）で統一  
- 内部リンク：`base.html` フッターに3本、`lp_client.html`に2本（発注者向け）、`lp_worker.html`に1本（受注者向け）  
- **今後の課題**：Googleサーチコンソールでインデックス登録をリクエストすること

---

## 実装済み機能

### プロフィール公開レベル（3段階）

- **レベル1（誰でも）**：アバター・屋号・エリア・ランクバッジ・役職  
- **レベル2（ログイン後）**：職種・年代・自己紹介・経験年数・資格・スキル  
- **レベル3（マッチング成立後）**：氏名・電話番号・LINE ID・メール・インボイス番号  
- **運営のみ**：本人確認書類・住所詳細

### 本人確認フォーム

- 住所詳細フィールド追加（`address_detail`）  
- 氏名・電話番号・住所を本人確認書類アップロード時に必須化  
- 承認時はメール通知なし・バッジ付与で確認

### 管理画面

- 管理者ボタン（ヘッダーに表示・未処理件数バッジ付き）  
- 差し戻し機能（理由セレクト＋フリーテキスト＋メール送信）

### パスワードリセット

- URL：`/accounts/password-reset/`  
- Django標準の `PasswordResetView` を使用

### お問い合わせフォーム

- 送信時に `kma.elchristo@gmail.com` にメール通知  
- ハニーポット・スパムキーワードフィルター・ブロックメールアドレス機能

### AI自己紹介文生成（2026年6月追加）

- プロフィール編集画面に「✨ AIで自己紹介文を生成する」ボタンを追加  
- 職種・経験年数・スキル等の入力情報をもとにClaude APIが100〜200文字の自己紹介文を自動生成  
- 実装ファイル：`accounts/views.py`（`generate_bio`ビュー）/ `accounts/urls.py` / `accounts/templates/accounts/profile_edit.html`  
- APIコスト：1回あたり約0.2〜0.5円  
- 環境変数：`ANTHROPIC_API_KEY`（Renderに設定済み）

### AI案件説明文生成（2026年6月追加）

- 案件投稿フォームに「✨ AIで説明文を生成する」ボタンを追加  
- 職種・場所・単価・期間などの入力情報をもとにClaude APIが150〜250文字の案件説明文を自動生成  
- 実装ファイル：`jobs/views.py`（`generate_job_description`ビュー）/ `jobs/urls.py` / `jobs/templates/jobs/create_job.html`  
- `requirements.txt` に `anthropic` 追加済み  
- 環境変数：`ANTHROPIC_API_KEY`（AI自己紹介文生成と共用）

### LINE公式アカウント

- あいさつメッセージ設定済み  
- リッチメニュー設定済み（左：仕事を探したい／右：職人を探したい）  
- 友だち追加URL：[https://lin.ee/5vt7bxm](https://lin.ee/5vt7bxm)  
- QRコード：両LP（client・worker）のCTAセクション下部に追加済み

### ランクアップページ（upgrade.html）

- URL：`/accounts/upgrade/`  
- 「3月末まで早期入会キャンペーン」などの古い文言を削除済み（2026年6月）  
- 現在は通常の料金比較表のみ表示

---

## Stripe決済（2026年6月に本番化完了）

- **本番モードに移行済み**。サンドボックスから本番商品（SILVER / GOLD / PLATINUM）を作成。  
- 価格IDは `settings.py` の `STRIPE_PRICE_IDS` に記載（本番用 `price_...` に更新済み）。  
- **Webhook**：本番エンドポイント `https://el-christo.jp/accounts/webhook/` を作成し、`checkout.session.completed` を含む推奨イベントを受信する設定済み。  
- 関連する環境変数（`STRIPE_PUBLISHABLE_KEY` / `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET`）はすべて本番用に更新済み。**値はRenderダッシュボードで確認すること。**

⚠️ 課金成功後にランクが上がらない場合は、Webhookが正しく動作しているかStripeダッシュボードの「Webhook」→「イベントログ」を確認する。

---

## メール設定

| 項目 | 内容 |
| :---- | :---- |
| 送信（Django） | [kma.elchristo@gmail.com](mailto:kma.elchristo@gmail.com)（SMTP） |
| 受信 | [info@el-christo.jp](mailto:info@el-christo.jp)（確認済み） |
| 送信（独自ドメイン） | SPF/DKIM未設定のためGmail宛てに届かない |
| ネームサーバー | 01〜04.dnsv.jp（Render側） |
| MXレコード | mail1033.onamae.ne.jp（設定済み・反映済み） |

---

## 残課題・TODO

- [ ] [info@el-christo.jp](mailto:info@el-christo.jp) の送信問題解決（SPF/DKIM設定）  
- [ ] Google広告の再検討（閑散期タイミング・AIキーワード訴求で再挑戦）  
- [ ] 登録者数の増加施策（広告資金の確保が最大の壁）  
- [ ] SEOコラム記事をGoogleサーチコンソールでインデックス登録リクエスト  
- [ ] Stripe本番決済の動作確認（実際に少額で決済テスト・ランクが上がるか確認）

---

## 環境変数（Render）

Renderのダッシュボード → kensetsu-app-1 → Environment に設定済み。 **実際の値はすべてRenderダッシュボードで確認すること（このメモには記載しない）。**

設定されている環境変数名：

- `SECRET_KEY`  
- `STRIPE_PUBLISHABLE_KEY`（本番用 `pk_live_...`・2026年6月更新）  
- `STRIPE_SECRET_KEY`（本番用 `sk_live_...`・2026年6月更新）  
- `STRIPE_WEBHOOK_SECRET`（本番用 `whsec_...`・2026年6月更新）  
- `AWS_ACCESS_KEY_ID`  
- `AWS_SECRET_ACCESS_KEY`  
- `AWS_STORAGE_BUCKET_NAME`  
- `DATABASE_URL`（Internal Database URL）  
- `RECAPTCHA_SECRET_KEY`  
- `PYTHON_VERSION`  
- `DJANGO_SUPERUSER_*`  
- `ANTHROPIC_API_KEY`（AI機能用・2026年6月追加）

⚠️ **注意**：`DATABASE_URL` を削除するとDBが切り替わりユーザーデータが消える。絶対に削除しないこと。

---

## 重要な教訓

1. 環境変数（特に `DATABASE_URL`）は削除前に必ず確認  
2. Renderのネームサーバー（dnsv.jp）を使っている場合、お名前.comのNaviのドメインDNS側にMXレコードを追加する必要がある  
3. お名前.comのレンタルサーバーのDNS設定はdnsv.jpから参照されない  
4. DjangoテンプレートでLPを直接Safariで開いてもQRコードは表示されない（`{% static %}`はDjangoサーバー経由でのみ処理される）  
5. LPにClaude Codeで`{% static %}`タグを使う場合は`{% load static %}`を先頭に忘れずに追加する  
6. GitHubトークン（`ghp_...`）やAPIキー・シークレットはチャットに貼り付けたら、作業後に必ず無効化・削除・ローテーションすること  
7. リポジトリがiCloud Drive上にあると `.git/refs` が破損することがある。iCloud同期外のフォルダ（例：`~/dev/`）への移動を検討

---

## 開発ヒストリー概要

| 時期 | 内容 |
| :---- | :---- |
| 2025年末〜2026年初 | Geminiと共同でDjangoベースのアプリを開発 |
| 2026年3月 | iOS App Store / Google Play Store で正式リリース |
| 2026年3〜4月 | Meta広告・Google広告を試みるも登録ゼロ |
| 2026年5月 | Claudeに切り替えて開発・運営サポート継続。名刺チラシで口コミ集客中 |
| 2026年6月 | キャンペーン文言の常設化・AI自己紹介文生成・AI案件説明文生成・SEOコラム記事3本追加・LINE QRコードをLPに追加・Stripe本番化完了 |

