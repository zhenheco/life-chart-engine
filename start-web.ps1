# start-web.ps1 — 啟動 Life Chart 本機網頁表單
# 雙擊或在 PowerShell 執行：會開瀏覽器到 http://127.0.0.1:8765
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $py (Join-Path $PSScriptRoot "webapp.py") @args
