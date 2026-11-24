# LINE Messages Skill for Codex & Claude Code

讓 Codex 與 Claude Code 透過 Skill 和唯讀 MCP 查詢你匯出的 LINE 訊息。Windows 登入後每 5 分鐘檢查匯入資料夾，也可用本機檢視器搜尋。

## 安裝

需要 Windows、Git、Python 3.11 以上（含 Tcl/Tk）與 LINE 桌面版。若要使用 MCP，先安裝並登入對應 CLI，確認 `codex` 或 `claude` 在 PATH 中。

在 GitHub 點 **Code** 複製網址，以實際網址替換下方第一行的佔位文字，再於 PowerShell 執行。

```powershell
git clone "REPOSITORY_HTTPS_URL"
cd line-messages-codex-claude-skill
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Setup.ps1 -Client Both
```

`-Client` 可選 `Codex`、`Claude`、`Both` 或 `None`。加入 `-NoBackground` 只使用手動匯入。Python 不在 PATH 時，加 `-Python` 並指定執行檔路徑。重開 AI 工具後，用 `codex mcp list` 或 `claude mcp list` 確認列出 `line-export-archive`。

<details>
<summary>手動註冊 MCP 或安裝選用技能</summary>

安裝後在專案根目錄執行相應指令。使用兩個用戶端時可各執行一次。

```powershell
$python = (Resolve-Path .\.venv\Scripts\python.exe).Path
$server = (Resolve-Path .\mcp_server.py).Path
codex mcp add line-export-archive -- $python $server
claude mcp add --transport stdio --scope user line-export-archive -- $python $server
```

將 `integrations/codex/line-export-messages` 複製到使用專案的 `.agents/skills/`，或把 `integrations/claude/line-export-messages` 複製到 `.claude/skills/`。若已有同名技能，先檢查內容再更新。

[Codex MCP](https://developers.openai.com/codex/mcp) · [Claude Code MCP](https://code.claude.com/docs/en/mcp)

</details>

## 匯入與查詢

1. 在 LINE 開啟聊天室，往上捲動載入所需期間，再從選單選「儲存聊天」。[LINE 匯出說明](https://help.line.me/line?contentId=20007388)
2. 把匯出的 `.txt` 複製到 `%LOCALAPPDATA%\LineExportArchive\inbox`。檔名即聊天室名稱，例如 `測試專案.txt`。同一聊天室補匯時沿用檔名。
3. 等待背景匯入，或開啟檢視器按「立即匯入」。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-Viewer.ps1
```

在檢視器選聊天室搜尋。也可問 Codex 或 Claude Code「到 LINE 查『測試專案』在 2025 年 1 月 7 日提到的『交付』，附上時間和訊息編號」。MCP 日期以匯出當地日期為準，查詢的結束日期不含當日。

## 資料不足

- **沒有紀錄**：按「立即匯入」，確認檔案小於等於 32 MiB，採 UTF-8 或帶 BOM 的 UTF-16，且格式如下。欄位以 Tab 分隔。
- **時間缺漏**：在 LINE 載入更早訊息後重新匯出。桌面版只匯出目前可顯示的歷史。
- **搜尋不到**：先清空關鍵字確認聊天室有資料，再試較短的字詞。封存只涵蓋已匯入的文字，媒體、OCR 與收回狀態不在支援範圍。

```text
2025/01/07 (Tue)
09:00	示範甲	交付時間為週五。
```

## 管理與解除安裝

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Manage-Service.ps1 -Action Status
```

將 `Status` 改為 `Stop`、`Start` 或 `Uninstall` 可暫停、恢復或移除背景工作。解除安裝時，另執行 `codex mcp remove line-export-archive` 或 `claude mcp remove --scope user line-export-archive`，再刪除專案。封存及匯出檔保留在 `%LOCALAPPDATA%\LineExportArchive`。

## LINE 規範與免責聲明

這是研究如何透過 Skill 與 MCP 查詢本機 LINE 文字匯出的獨立專案，與 LINE 或 LY Corporation 無隸屬關係。請遵守適用法律與 LINE 條款，只處理有權使用的聊天紀錄。MCP 回傳片段會進入所用 AI 工具的模型上下文，敏感紀錄請用本機檢視器。

專案依 MIT 授權按現狀提供。匯出範圍取決於 LINE 當下可顯示的訊息。請在使用查詢結果前核對原始紀錄。

[LINE 通用服務條款](https://terms.line.me/line_terms?lang=zh-Hant) · [臺灣聊天服務特別條款](https://terms.line.me/line_terms_notice?lang=zh-Hant) · [LY Corporation 隱私權政策](https://www.lycorp.co.jp/zh-TW/company/privacypolicy/) · [MIT 授權](LICENSE)
