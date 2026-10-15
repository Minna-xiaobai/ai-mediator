# AI 溝通調解助手（本機／區網 MVP）

本工具適用於任何需要溝通的兩人，例如家人、朋友、同事、伴侶或其他關係，不限於戀愛／伴侶情境。

## 安裝與啟動

在 `AI溝通調解助手` 資料夾的 PowerShell 執行。目前虛擬環境仍位於上一層 `Documents` 資料夾：

```powershell
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

預設只監聽本機 `127.0.0.1`。若要讓同一個可信私人區網中的另一台裝置連線，才使用下方的區網啟動指令。

到 Groq Console 建立 API Key，並只存入本機 `.env`：

```env
GROQ_API_KEY=gsk_你的Groq金鑰
```

## 兩人配對

1. A 在自己的瀏覽器建立帳號並登入，按「建立新配對」，把一次性邀請碼私下交給 B。
2. B 在自己的瀏覽器建立另一個帳號並登入，輸入邀請碼加入。
3. 雙方各自與私人 AI 助理聊天、產生並確認摘要；只有雙方都明確同意後，才能啟動 AI 代表交流並生成共識報告。每個配對只會儲存一份共同報告，生成期間會阻止重複請求；若生成失敗，另一方可在鎖定逾時或請求釋放後重試。
4. 配對任一方可在「配對資料與刪除」刪除整個配對及其摘要／報告。

邀請碼 24 小時後失效且只能使用一次。帳號密碼以 scrypt 雜湊後存入本機 SQLite 資料庫 `mediator.sqlite3`。原始聊天只存於各自 Streamlit 瀏覽器工作階段的記憶體，不寫入資料庫；登出或工作階段結束後，聊天可能無法復原。建立摘要、AI 對話及生成報告時，相關內容會傳送至 Groq。

## 區域網路測試

在信任的私人網路中，於主機執行：

```powershell
streamlit run app.py --server.address 0.0.0.0
```

另一台裝置使用 `http://主機的區域網路 IP:8501` 開啟。可用 `ipconfig` 查看主機 IPv4 位址；若 Windows 防火牆詢問，只允許私人網路存取。

此版本沒有 TLS、電子郵件驗證、密碼重設或正式部署所需的安全強化，僅供本機／可信區網原型測試。不要在公用 Wi-Fi 或網際網路上開放，也不要輸入高度敏感資訊。正式上線前需加入 HTTPS、穩固的登入工作階段、備份／保留政策及安全審查。

資料庫預設為專案目錄的 `mediator.sqlite3`，已由 `.gitignore` 排除。可透過 `MEDIATOR_DB_PATH` 環境變數指定其他本機路徑。

## 執行測試

```powershell
..\.venv\Scripts\python.exe -m unittest -v test_storage test_safety
```
