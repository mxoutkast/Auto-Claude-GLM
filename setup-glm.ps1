# Auto-Claude GLM Setup Script
# Configures GLM as the default AI provider

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Auto-Claude GLM Setup" -ForegroundColor Cyan
Write-Host "  100x cheaper than Claude!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
$envFile = "apps\backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    New-Item -Path $envFile -ItemType File -Force | Out-Null
}

# Check current configuration
$currentProvider = Select-String -Path $envFile -Pattern "^AI_PROVIDER=" -ErrorAction SilentlyContinue
$currentKey = Select-String -Path $envFile -Pattern "^ZHIPUAI_API_KEY=" -ErrorAction SilentlyContinue

if ($currentProvider -and $currentKey) {
    Write-Host "✓ GLM is already configured!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Current settings:" -ForegroundColor Cyan
    Write-Host "  $($currentProvider.Line)" -ForegroundColor Gray
    Write-Host "  ZHIPUAI_API_KEY=***" -ForegroundColor Gray
    Write-Host ""
    
    $reconfigure = Read-Host "Do you want to reconfigure? (y/N)"
    if ($reconfigure -ne "y" -and $reconfigure -ne "Y") {
        Write-Host ""
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Get API key
Write-Host "Get your GLM API key from:" -ForegroundColor Cyan
Write-Host "  • Z.AI: https://api.z.ai" -ForegroundColor White
Write-Host "  • ZhipuAI: https://open.bigmodel.cn" -ForegroundColor White
Write-Host ""

$apiKey = Read-Host "Enter your GLM API key"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host ""
    Write-Host "✗ API key is required!" -ForegroundColor Red
    exit 1
}

# Update or add AI_PROVIDER
Write-Host ""
Write-Host "Configuring GLM..." -ForegroundColor Yellow

$envContent = Get-Content $envFile -Raw
if ($envContent -match "AI_PROVIDER=") {
    $envContent = $envContent -replace "AI_PROVIDER=.*", "AI_PROVIDER=glm"
} else {
    $envContent += "`nAI_PROVIDER=glm"
}

# Update or add ZHIPUAI_API_KEY
if ($envContent -match "ZHIPUAI_API_KEY=") {
    $envContent = $envContent -replace "ZHIPUAI_API_KEY=.*", "ZHIPUAI_API_KEY=$apiKey"
} else {
    $envContent += "`nZHIPUAI_API_KEY=$apiKey"
}

# Save configuration
Set-Content -Path $envFile -Value $envContent.Trim()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ GLM Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration saved to: $envFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Install ZhipuAI SDK:" -ForegroundColor White
Write-Host "     cd apps\backend" -ForegroundColor Gray
Write-Host "     .\.venv\Scripts\pip.exe install zhipuai" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start the app:" -ForegroundColor White
Write-Host "     npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Select GLM-4.7 profile in agent settings" -ForegroundColor White
Write-Host ""
Write-Host "Cost savings: ~100x cheaper than Claude!" -ForegroundColor Green
Write-Host ""
