# Daily CYPHERiSLIVE blog run (registered as Windows scheduled task "CYPHERiSLIVE-DailyBlog").
# Starts a headless Claude Code session that follows out/blog/DAILY.md. Log: out/blog/daily/run-YYYY-MM-DD.log
$ErrorActionPreference = "Stop"
$root = "e:\GiHub Clones\Claude animated\claudeAnimatedShorts"
Set-Location $root
New-Item -ItemType Directory -Force "$root\out\blog\daily" | Out-Null
$log = "$root\out\blog\daily\run-$(Get-Date -Format yyyy-MM-dd).log"

# the VS Code extension folder name changes with updates, so pick the newest claude.exe
$claude = Get-ChildItem "$env:USERPROFILE\.vscode\extensions" -Directory -Filter "anthropic.claude-code*" |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object { Join-Path $_.FullName "resources\native-binary\claude.exe" } |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $claude) { "claude.exe not found" | Out-File $log -Append -Encoding utf8; exit 1 }

$prompt = "Follow out/blog/DAILY.md exactly: find today's verified gaming news and publish 2 new bilingual posts to the CYPHERiSLIVE blog, verify them live, and write the daily log. Today is $(Get-Date -Format yyyy-MM-dd)."
"=== start $(Get-Date -Format s) using $claude" | Out-File $log -Append -Encoding utf8
$env:PYTHONIOENCODING = "utf-8"
& $claude -p $prompt --allowedTools "Bash,PowerShell,Read,Write,Edit,Glob,Grep,WebSearch,WebFetch" --permission-mode acceptEdits --max-turns 120 2>&1 | Out-File $log -Append -Encoding utf8
"=== end $(Get-Date -Format s) exit $LASTEXITCODE" | Out-File $log -Append -Encoding utf8
