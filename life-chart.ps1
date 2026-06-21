# life-chart.ps1 — Windows launcher for life-chart-engine
# 用法範例:
#   .\life-chart.ps1 --json --name "Allen" --gender 男 --date 1986-07-10 --time 08:53 --tz 8 --lat 24.0838 --lon 120.4046 --target 2025-01-01
#   .\life-chart.ps1 --name "Allen" --gender 男 --date 1986-07-10 --time 08:53 --tz 8 --lat 24.0838 --lon 120.4046   # 省略 --json = 人類可讀報告
$env:PYTHONUTF8 = "1"   # 讓 Markdown 報告能輸出 ℞ 等符號 (避開 cp950 錯誤)
$py  = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$eng = Join-Path $PSScriptRoot "scripts\chart_engine.py"
& $py $eng @args
