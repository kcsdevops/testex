# Exemplo prático de uso dos testes de conectividade
# Execute este script para demonstrar o sistema de testes

Write-Host "🧪 DEMONSTRAÇÃO DE TESTES DE CONECTIVIDADE TESTEX" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

# Função para pause elegante
function Wait-UserInput {
    param([string]$Message = "Pressione qualquer tecla para continuar...")
    Write-Host $Message -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Write-Host ""
}

# 1. Verificar se o laboratório está funcionando
Write-Host "1️⃣ VERIFICANDO STATUS ATUAL DO LABORATÓRIO" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
.\lab.ps1 status
Wait-UserInput

# 2. Testar conectividade completa
Write-Host "2️⃣ EXECUTANDO TESTES DE CONECTIVIDADE COMPLETOS" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
.\Test-Laboratory.ps1 -Detailed
Wait-UserInput

# 3. Demonstrar início do laboratório com testes
Write-Host "3️⃣ INICIANDO LABORATÓRIO (se não estiver rodando)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Iniciando laboratório em modo detached..." -ForegroundColor Yellow
.\lab.ps1 start

Write-Host ""
Write-Host "Aguardando 30 segundos para os serviços iniciarem..." -ForegroundColor Yellow
Start-Sleep 30

Write-Host ""
Write-Host "Executando testes com espera por serviços..." -ForegroundColor Yellow
.\Test-Laboratory.ps1 -WaitForServices -MaxWaitMinutes 3 -Detailed
Wait-UserInput

# 4. Mostrar diferentes opções de teste
Write-Host "4️⃣ OPÇÕES AVANÇADAS DE TESTE" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Teste básico (sem detalhes):" -ForegroundColor Yellow
.\Test-Laboratory.ps1

Write-Host ""
Write-Host "Teste com correção automática:" -ForegroundColor Yellow
.\Test-Laboratory.ps1 -FixIssues -Detailed

Wait-UserInput

# 5. Finalização
Write-Host "5️⃣ DEMONSTRAÇÃO CONCLUÍDA" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Testes de conectividade implementados com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📖 Comandos úteis para o dia a dia:" -ForegroundColor Cyan
Write-Host "   .\lab.ps1 test                    # Teste rápido" -ForegroundColor White
Write-Host "   .\Test-Laboratory.ps1 -Detailed  # Teste detalhado" -ForegroundColor White
Write-Host "   .\Test-Laboratory.ps1 -FixIssues # Teste com correção automática" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Endpoints do laboratório:" -ForegroundColor Cyan
Write-Host "   SQL Server: localhost:1433 (sa/TestexSQL2024!)" -ForegroundColor White
Write-Host "   LDAP Admin: http://localhost:8080" -ForegroundColor White
Write-Host "   UMA API: http://localhost:5000" -ForegroundColor White
Write-Host "   MailHog: http://localhost:8025" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Laboratório TESTEX pronto para uso!" -ForegroundColor Green