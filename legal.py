"""Privacy Policy and Terms of Use shown in the app (zh / en).

These are a starting template for a beta, not legal advice; have them reviewed
before charging users or launching widely. {contact} is the operator's contact
email (CONTACT_EMAIL setting) and {updated} the last-revised date.
"""

UPDATED = "2026-10-27"

PRIVACY = {
    "zh": """\
_最後更新：{updated}_

**我們收集的資料**
- **帳號**：帳號名稱，以及經 scrypt 雜湊處理的密碼（我們看不到你的密碼原文）。
- **你同意儲存的內容**：你儲存的摘要、分享同意狀態，以及雙方的共同報告。
- **私人聊天**：只暫存在你目前的瀏覽器工作階段記憶體中，**不會寫入資料庫**，重新整理或登出後即消失。

**資料如何使用與傳送**
- 為了產生 AI 回覆、摘要與報告，相關內容會傳送給 AI 服務供應商 **Groq, Inc.**（美國）處理。
- 帳號、摘要與報告儲存在雲端資料庫供應商的伺服器上（可能位於台灣以外的地區）。
- 我們不販售你的資料，不用於廣告，也不會分享給配對對象以外的人；摘要只有在你勾選同意後才會讓對方與調解 AI 看到。

**保存與刪除**
- 摘要與報告會保存到你或配對對象刪除該配對為止。
- 你可以隨時在「配對資料與刪除」刪除配對，或在側邊欄「帳號設定」永久刪除帳號；刪除後無法復原。

**安全**
- 傳輸使用 HTTPS 加密，資料庫存取受密碼保護。但沒有任何系統能保證絕對安全，請勿輸入真實姓名、聯絡方式、身分證號等高度敏感資訊。

**年齡**
- 本服務僅供年滿 18 歲的使用者使用。

**聯絡我們**
- 對隱私有任何問題或要求，請寫信至 {contact}。
""",
    "en": """\
_Last updated: {updated}_

**What we collect**
- **Account**: your username and a scrypt hash of your password (we never see the password itself).
- **Content you choose to save**: summaries you save, your sharing consent, and the shared report for each pairing.
- **Private chat**: kept only in your current browser session's memory. It is **never written to our database** and disappears when you refresh or log out.

**How data is used and shared**
- To generate AI replies, summaries and reports, the relevant text is sent to our AI provider, **Groq, Inc.** (United States), for processing.
- Accounts, summaries and reports are stored with our cloud database provider, possibly outside your country.
- We do not sell your data or use it for advertising, and we don't share it with anyone other than your pairing partner. A summary is shown to the other person and the mediation AI only after you consent.

**Retention and deletion**
- Summaries and reports are kept until you or your partner delete the pairing.
- You can delete a pairing at any time under "Pairing data & deletion", or permanently delete your account under "Account" in the sidebar. Deletion cannot be undone.

**Security**
- Traffic is encrypted with HTTPS and database access is password protected. No system is perfectly secure, so please don't enter real names, contact details, ID numbers or other highly sensitive information.

**Age**
- This service is for people aged 18 or over.

**Contact**
- For any privacy question or request, email {contact}.
""",
}

TERMS = {
    "zh": """\
_最後更新：{updated}_

1. **服務性質**：AI 溝通調解助手是以 AI 產生溝通建議的工具，目前為**試用版**。它**不是**心理諮商、醫療、法律或其他專業服務，AI 的內容可能不正確或不適合你的情況，請自行判斷。
2. **緊急狀況**：本服務無法處理緊急或人身安全問題。若你或他人有立即危險，請撥打 110／119 或當地緊急電話，或聯繫 113 保護專線、1925 安心專線。涉及暴力、威脅或自我傷害的情況不適合使用本服務進行調解。
3. **使用資格**：你必須年滿 18 歲。請妥善保管帳號密碼，帳號下的活動由你負責。
4. **使用規範**：請勿用於騷擾、威脅、操控或監控他人；請勿輸入他人的個人資料或違法內容；請勿嘗試破壞、濫用或大量自動存取本服務。
5. **你的內容**：你保有自己輸入內容的權利，並授權我們為了提供服務而處理這些內容（包含傳送給 AI 供應商）。
6. **服務變更**：試用期間功能、可用性與資料可能變動或中斷，我們會盡力但不保證資料不遺失。我們可以因違反本條款而停用帳號。
7. **責任限制**：在法律允許的最大範圍內，本服務依「現狀」提供，對於因使用或依賴 AI 建議所產生的任何損失，我們不負賠償責任。
8. **準據法**：本條款以中華民國（台灣）法律為準據法。
9. **聯絡**：{contact}
""",
    "en": """\
_Last updated: {updated}_

1. **What this is**: AI Mediator is a tool that uses AI to suggest ways to communicate, currently in **beta**. It is **not** therapy, counselling, medical, legal or any other professional service. AI output may be wrong or unsuitable for your situation; use your own judgement.
2. **Emergencies**: This service cannot handle emergencies or safety issues. If you or someone else is in immediate danger, call your local emergency number or a crisis line (see findahelpline.com). Situations involving violence, threats or self-harm are not suitable for mediation through this service.
3. **Eligibility**: You must be 18 or older. Keep your password safe; you are responsible for activity under your account.
4. **Acceptable use**: Don't use the service to harass, threaten, manipulate or monitor anyone; don't enter other people's personal data or unlawful content; don't attempt to disrupt, abuse or scrape the service.
5. **Your content**: You keep the rights to what you write and let us process it to provide the service, including sending it to our AI provider.
6. **Changes**: During the beta, features, availability and data may change or be interrupted. We try hard not to lose data but can't guarantee it. We may suspend accounts that break these terms.
7. **Liability**: To the extent permitted by law, the service is provided "as is", and we are not liable for any loss arising from using or relying on AI suggestions.
8. **Governing law**: These terms are governed by the laws of Taiwan (Republic of China).
9. **Contact**: {contact}
""",
}

PRIVACY["ja"] = """\
_最終更新日：{updated}_

**収集する情報**
- **アカウント**：ユーザー名と、scrypt でハッシュ化したパスワード（パスワードそのものは私たちにも見えません）。
- **保存を選んだ内容**：保存した要約、共有への同意状況、各ペアの共同レポート。
- **プライベートチャット**：現在のブラウザのセッションのメモリにのみ一時保存され、**データベースには保存されません**。再読み込みやログアウトで消えます。

**情報の利用と送信**
- AI の返信・要約・レポートを作成するため、関連する内容を AI サービス提供者 **Groq, Inc.**（米国）に送信して処理します。
- アカウント、要約、レポートはクラウドデータベース事業者のサーバー（日本国外の場合があります）に保存されます。
- 情報を販売したり広告に使ったりすることはなく、ペアの相手以外に共有することもありません。要約は、あなたが同意した後にのみ相手と調停 AI に表示されます。

**保存期間と削除**
- 要約とレポートは、あなたまたは相手がそのペアを削除するまで保存されます。
- 「ペアのデータと削除」からいつでもペアを削除でき、サイドバーの「アカウント設定」からアカウントを完全に削除できます。削除は元に戻せません。

**セキュリティ**
- 通信は HTTPS で暗号化され、データベースへのアクセスはパスワードで保護されています。ただし完全に安全なシステムはないため、本名・連絡先・各種番号など機密性の高い情報は入力しないでください。

**年齢**
- 本サービスは 18 歳以上の方のみご利用いただけます。

**お問い合わせ**
- プライバシーに関するご質問やご要望は {contact} までご連絡ください。
"""

TERMS["ja"] = """\
_最終更新日：{updated}_

1. **サービスの性質**：AI コミュニケーション調停アシスタントは、AI がコミュニケーションの提案を行うツールで、現在**ベータ版**です。カウンセリング、医療、法律その他の専門サービスでは**ありません**。AI の内容は誤っていたり、あなたの状況に合わなかったりする場合があるため、ご自身で判断してください。
2. **緊急時**：本サービスは緊急事態や身の安全の問題に対応できません。あなたや他の人に差し迫った危険がある場合は 110 番・119 番、または最寄りの緊急窓口に連絡してください（相談窓口：いのちの電話、DV 相談ナビ #8008 など）。暴力・脅迫・自傷を伴う状況は、本サービスによる調停には適しません。
3. **利用資格**：18 歳以上である必要があります。パスワードは適切に管理してください。アカウントでの行為はご自身の責任となります。
4. **禁止事項**：他人への嫌がらせ、脅迫、操作、監視に使わないでください。他人の個人情報や違法な内容を入力しないでください。サービスの妨害、濫用、大量の自動アクセスを試みないでください。
5. **あなたのコンテンツ**：入力した内容の権利はあなたに残ります。サービス提供のため（AI 事業者への送信を含む）にその内容を処理することを許諾していただきます。
6. **サービスの変更**：ベータ期間中は機能、提供状況、データが変更・中断される場合があります。データを失わないよう努めますが、保証はできません。本規約に違反したアカウントは停止することがあります。
7. **責任の制限**：法律で認められる最大限の範囲で、本サービスは「現状のまま」提供され、AI の提案の利用または依拠によって生じた損害について責任を負いません。
8. **準拠法**：本規約は台湾（中華民国）法を準拠法とします。
9. **お問い合わせ**：{contact}
"""
