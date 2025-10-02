# Script PowerShell para inicializar o laboratório no Windows

Write-Host "🚀 Iniciando Laboratório de Automação - TERMINO DE CONTRATO" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# Verificar se o Docker está rodando
try {
    docker info | Out-Null
    Write-Host "✅ Docker está rodando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está rodando. Por favor, inicie o Docker Desktop primeiro." -ForegroundColor Red
    exit 1
}

# Navegar para o diretório do laboratório
Set-Location -Path (Join-Path $PSScriptRoot ".")

# Parar containers existentes se houver
Write-Host "🧹 Limpando containers anteriores..." -ForegroundColor Yellow
docker-compose down -v 2>$null

# Construir e iniciar os serviços
Write-Host "🏗️  Construindo e iniciando serviços..." -ForegroundColor Yellow
docker-compose up -d --build

# Aguardar inicialização dos serviços
Write-Host "⏳ Aguardando inicialização dos serviços..." -ForegroundColor Yellow

# Aguardar SQL Server
Write-Host "📊 Aguardando SQL Server..." -ForegroundColor Cyan
do {
    Start-Sleep -Seconds 5
    $sqlReady = docker exec lab-sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "LabPassword123!" -Q "SELECT 1" 2>$null
    if (-not $sqlReady) {
        Write-Host "   ... SQL Server ainda inicializando" -ForegroundColor Gray
    }
} while (-not $sqlReady)
Write-Host "✅ SQL Server pronto!" -ForegroundColor Green

# Aguardar Active Directory
Write-Host "🔐 Aguardando Active Directory..." -ForegroundColor Cyan
Start-Sleep -Seconds 30  # AD precisa de mais tempo para configurar
Write-Host "✅ Active Directory pronto!" -ForegroundColor Green

# Aguardar File Server
Write-Host "📁 Aguardando File Server..." -ForegroundColor Cyan
do {
    Start-Sleep -Seconds 5
    $fileReady = docker exec lab-file-server smbclient -L localhost -U testuser%LabPassword123! 2>$null
    if (-not $fileReady) {
        Write-Host "   ... File Server ainda inicializando" -ForegroundColor Gray
    }
} while (-not $fileReady)
Write-Host "✅ File Server pronto!" -ForegroundColor Green

# Configurar AD com usuários de teste
Write-Host "👥 Configurando usuários de teste no AD..." -ForegroundColor Yellow
docker exec lab-ad-server bash /scripts/setup-ad.sh

# Criar arquivos de teste
Write-Host "📄 Criando arquivos de teste..." -ForegroundColor Yellow
docker exec lab-file-server bash /file-init/create-test-files.sh

# Executar inicialização do banco de dados
Write-Host "🗄️  Inicializando banco de dados..." -ForegroundColor Yellow
docker exec lab-sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "LabPassword123!" -i /docker-entrypoint-initdb.d/init.sql

Write-Host ""
Write-Host "🎉 LABORATÓRIO INICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 SERVIÇOS DISPONÍVEIS:" -ForegroundColor White
Write-Host "   • SQL Server:        localhost:1433 (sa/LabPassword123!)" -ForegroundColor Cyan
Write-Host "   • Active Directory:  localhost:389  (LAB.LOCAL)" -ForegroundColor Cyan
Write-Host "   • File Server:       localhost:445  (testuser/LabPassword123!)" -ForegroundColor Cyan
Write-Host "   • Jenkins:           http://localhost:8080 (admin/LabPassword123!)" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 PARA EXECUTAR TESTES:" -ForegroundColor White
Write-Host "   docker exec -it lab-python-runner python /app/lab_simulator.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 PARA VER LOGS:" -ForegroundColor White
Write-Host "   docker-compose logs -f [service_name]" -ForegroundColor Yellow
Write-Host ""
Write-Host "🛑 PARA PARAR O LAB:" -ForegroundColor White
Write-Host "   docker-compose down -v" -ForegroundColor Yellow
Write-Host ""

# Perguntar se quer iniciar o simulador
$response = Read-Host "Deseja iniciar o simulador interativo agora? (s/n)"
if ($response -eq 's' -or $response -eq 'S' -or $response -eq 'sim') {
    Write-Host "🔄 Iniciando simulador interativo..." -ForegroundColor Green
    docker exec -it lab-python-runner python /app/lab_simulator.py
}