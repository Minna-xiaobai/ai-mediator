# AI 溝通調解助手 / AI Mediator

本工具適用於任何需要溝通的兩人，例如家人、朋友、同事、伴侶或其他關係，不限於戀愛／伴侶情境。介面支援**繁體中文、英文與日文**（依瀏覽器語言自動選擇，可在側邊欄切換；翻譯在 [i18n.py](i18n.py)）；AI 會用使用者的語言回覆，若雙方摘要語言不同，報告會同時以兩種語言撰寫。危險內容偵測與求助資源也涵蓋三種語言（台灣、日本與國際專線）。

## 本機啟動

在 `AI溝通調解助手` 資料夾的 PowerShell 執行。目前虛擬環境仍位於上一層 `Documents` 資料夾：

```powershell
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py --server.address 127.0.0.1
```

`--server.address 127.0.0.1` 讓程式只在本機監聽。到 Groq Console 建立 API Key，並只存入本機 `.env`：

```env
GROQ_API_KEY=gsk_你的Groq金鑰
```

本機未設定 `DATABASE_URL` 時，資料存在專案目錄的 `mediator.sqlite3`（已由 `.gitignore` 排除，可用 `MEDIATOR_DB_PATH` 指定其他路徑）。

## 雲端部署（Streamlit Community Cloud + Supabase，免費方案）

1. **建立資料庫**：到 [supabase.com](https://supabase.com) 註冊並建立新專案（記下資料庫密碼，區域可選 Tokyo 或 Singapore）。專案建立後按上方 **Connect**，複製 **Transaction pooler** 的連線字串（port 6543），把 `[YOUR-PASSWORD]` 換成你的資料庫密碼。資料表會在第一次啟動時自動建立，並開啟 Row Level Security，避免被 Supabase 的公開 API 讀取。
2. **推送程式碼**：把最新程式碼 push 到 GitHub（`.env`、`secrets.toml`、`mediator.sqlite3` 都不會被上傳）。
3. **部署**：到 [share.streamlit.io](https://share.streamlit.io) 用 GitHub 登入 → **Create app** → 選擇此 repo、分支 `main`、主檔案 `app.py`。在 **Advanced settings** 選 Python 3.12，並在 **Secrets** 貼上 [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) 的內容（填入真實值）。
4. 部署完成後會得到 `https://xxxx.streamlit.app` 網址，可直接分享。

設定值（`.env`、環境變數或 Streamlit secrets 皆可）：

| 名稱 | 必填 | 說明 |
|---|---|---|
| `GROQ_API_KEY` | 是 | Groq API Key |
| `DATABASE_URL` | 雲端必填 | PostgreSQL 連線字串；未設定則使用本機 SQLite |
| `BETA_ACCESS_CODE` | 否 | 設定後，註冊需輸入此試用通行碼（試用期間可控制 AI 用量） |
| `CONTACT_EMAIL` | 建議 | 顯示在隱私權政策與使用條款中的聯絡信箱 |

## 兩人配對

1. A 在自己的瀏覽器建立帳號並登入，按「建立新配對」，把一次性邀請碼私下交給 B。
2. B 在自己的瀏覽器建立另一個帳號並登入，輸入邀請碼加入。
3. 雙方各自與私人 AI 助理聊天、產生並確認摘要；只有雙方都明確同意後，才能啟動 AI 代表交流並生成共識報告。每個配對只會儲存一份共同報告，生成期間會阻止重複請求；若生成失敗，另一方可在鎖定逾時或請求釋放後重試。
4. 配對任一方可在「配對資料與刪除」刪除整個配對及其摘要／報告；使用者也可在側邊欄「帳號設定」永久刪除帳號。

註冊時需勾選同意使用條款與隱私權政策（內容在 [legal.py](legal.py)，屬試用版範本，正式收費前建議請專業人士審閱）。邀請碼 24 小時後失效且只能使用一次。密碼以 scrypt 雜湊後儲存。原始聊天只存於各自 Streamlit 瀏覽器工作階段的記憶體，不寫入資料庫。建立摘要、AI 對話及生成報告時，相關內容會傳送至 Groq。

## 尚未完成（正式收費前）

- 忘記密碼／Email 驗證、重新整理後保持登入
- 每位使用者的 AI 用量上限（目前靠 `BETA_ACCESS_CODE` 控制）
- 付費機制

## 執行測試

```powershell
..\.venv\Scripts\python.exe -m unittest -v test_storage test_safety test_i18n
```

要對 PostgreSQL 執行同一套儲存測試，設定 `MEDIATOR_TEST_DATABASE_URL` 指向一個**空的測試資料庫**（測試會刪除所有資料表，切勿指向正式資料庫）。
