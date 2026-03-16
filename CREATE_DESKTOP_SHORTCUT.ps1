# Create Desktop Shortcut for SRP SmartRecruit v3.2
# Run this script once to create a shortcut on your desktop

$currentPath = $PSScriptRoot
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "SRP SmartRecruit v3.2.lnk"

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = Join-Path $currentPath "START_WITH_NGROK.bat"
$Shortcut.WorkingDirectory = $currentPath
$Shortcut.Description = "SRP SmartRecruit v3.2 - AI-Powered ATS with Public URL"
$Shortcut.IconLocation = "imageres.dll,1"  # Windows globe icon
$Shortcut.Save()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Desktop Shortcut Created!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $shortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Double-click the shortcut to start:" -ForegroundColor Yellow
Write-Host "  - FastAPI server (port 5003)" -ForegroundColor White
Write-Host "  - Ngrok public URL (7-day access)" -ForegroundColor White
Write-Host "  - Automatic team sharing link" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
