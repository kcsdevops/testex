# COMANDOS PRINCIPAIS DO PROJETO TESTEX
# Execute estes comandos para operar o sistema de automação

Write-Host "🚀 PROJETO TESTEX - COMANDOS PRINCIPAIS" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

Write-Host ""
Write-Host "📋 COMANDOS DISPONÍVEIS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. CONFIGURAÇÃO INICIAL:" -ForegroundColor Cyan
Write-Host "   .\Setup-Credentials.ps1" -ForegroundColor White
Write-Host ""
Write-Host "2. GUIA RÁPIDO:" -ForegroundColor Cyan  
Write-Host "   .\Start-QuickGuide.ps1" -ForegroundColor White
Write-Host ""
Write-Host "3. TERMINAÇÃO DE CONTRATO:" -ForegroundColor Cyan
Write-Host "   .\TerminoContrato-Main.ps1 -ClienteId CL001" -ForegroundColor White
Write-Host ""
Write-Host "4. VALIDAÇÃO DO SISTEMA:" -ForegroundColor Cyan
Write-Host "   .\Test-SystemValidation.ps1" -ForegroundColor White
Write-Host ""
Write-Host "5. LABORATÓRIO DE DEMONSTRAÇÃO:" -ForegroundColor Cyan
Write-Host "   cd laboratorio" -ForegroundColor White
Write-Host "   .\start-demo.ps1" -ForegroundColor White
Write-Host ""
Write-Host "6. DEMONSTRAÇÃO RÁPIDA:" -ForegroundColor Cyan
Write-Host "   python demo.py" -ForegroundColor White
Write-Host ""
Write-Host "Pressione qualquer tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")