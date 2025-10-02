# TESTEX Laboratory Scripts
# Scripts para gerenciamento do ambiente de laboratório

# Função para verificar Docker
function Test-DockerRunning {
    try {
        $null = docker version 2>$null
        return $true
    }
    catch {
        return $false
    }
}

# Função para exibir status colorido
function Write-Status {
    param(
        [string]$Service,
        [string]$Status,
        [string]$Color = "White"
    )
    
    $statusIcon = switch ($Status) {
        "Running" { "🟢" }
        "Stopped" { "🔴" }
        "Starting" { "🟡" }
        "Error" { "❌" }
        default { "⚪" }
    }
    
    Write-Host "$statusIcon $Service`: " -NoNewline
    Write-Host $Status -ForegroundColor $Color
}

# Função principal
function Invoke-LabCommand {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("start", "stop", "status", "logs", "restart", "clean", "help")]
        [string]$Action,
        
        [string]$Service = "",
        [switch]$Detached = $true,
        [switch]$Build = $false
    )
    
    $labPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $labPath
    
    # Verificar se Docker está instalado e rodando
    if (-not (Test-DockerRunning)) {
        Write-Host "❌ Docker não está instalado ou não está rodando!" -ForegroundColor Red
        Write-Host "   Instale o Docker Desktop e inicie-o antes de usar o laboratório." -ForegroundColor Yellow
        return
    }
    
    switch ($Action) {
        "start" {
            Write-Host "🚀 Iniciando Laboratório TESTEX..." -ForegroundColor Green
            
            $buildFlag = if ($Build) { "--build" } else { "" }
            $detachedFlag = if ($Detached) { "-d" } else { "" }
            
            if ($Service) {
                Write-Host "   Iniciando serviço: $Service" -ForegroundColor Cyan
                docker-compose up $detachedFlag $buildFlag $Service
            }
            else {
                Write-Host "   Iniciando todos os serviços..." -ForegroundColor Cyan
                docker-compose up $detachedFlag $buildFlag
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Laboratório iniciado com sucesso!" -ForegroundColor Green
                Write-Host ""
                Write-Host "🔗 Serviços disponíveis:" -ForegroundColor Yellow
                Write-Host "   • SQL Server: localhost:1433 (sa/TestexSQL2024!)" -ForegroundColor White
                Write-Host "   • LDAP Admin: http://localhost:8080" -ForegroundColor White
                Write-Host "   • UMA API: http://localhost:5000" -ForegroundColor White
                Write-Host "   • MailHog: http://localhost:8025" -ForegroundColor White
                Write-Host "   • File Server: \\localhost\testex (testuser/testpass)" -ForegroundColor White
                Write-Host ""
                Write-Host "💡 Execute 'lab test' para verificar conectividade dos serviços" -ForegroundColor Cyan
            }
            else {
                Write-Host "❌ Erro ao iniciar laboratório!" -ForegroundColor Red
            }
        }
        
        "stop" {
            Write-Host "🛑 Parando Laboratório TESTEX..." -ForegroundColor Yellow
            
            if ($Service) {
                Write-Host "   Parando serviço: $Service" -ForegroundColor Cyan
                docker-compose stop $Service
            }
            else {
                Write-Host "   Parando todos os serviços..." -ForegroundColor Cyan
                docker-compose down
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Laboratório parado com sucesso!" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Erro ao parar laboratório!" -ForegroundColor Red
            }
        }
        
        "status" {
            Write-Host "📊 Status do Laboratório TESTEX" -ForegroundColor Cyan
            Write-Host "=================================" -ForegroundColor Cyan
            
            try {
                $containers = docker-compose ps --format json | ConvertFrom-Json
                
                if ($containers) {
                    foreach ($container in $containers) {
                        $serviceName = $container.Service
                        $state = $container.State
                        
                        $color = switch ($state) {
                            "running" { "Green" }
                            "exited" { "Red" }
                            "restarting" { "Yellow" }
                            default { "Gray" }
                        }
                        
                        Write-Status -Service $serviceName -Status $state -Color $color
                    }
                }
                else {
                    Write-Host "⚪ Nenhum serviço do laboratório está rodando" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "❌ Erro ao obter status dos serviços" -ForegroundColor Red
                Write-Host "   Verifique se o Docker está rodando" -ForegroundColor Yellow
            }
        }
        
        "logs" {
            Write-Host "📋 Logs do Laboratório TESTEX" -ForegroundColor Cyan
            
            if ($Service) {
                Write-Host "   Exibindo logs do serviço: $Service" -ForegroundColor Yellow
                docker-compose logs -f $Service
            }
            else {
                Write-Host "   Exibindo logs de todos os serviços..." -ForegroundColor Yellow
                docker-compose logs -f
            }
        }
        
        "restart" {
            Write-Host "🔄 Reiniciando Laboratório TESTEX..." -ForegroundColor Yellow
            
            if ($Service) {
                Write-Host "   Reiniciando serviço: $Service" -ForegroundColor Cyan
                docker-compose restart $Service
            }
            else {
                Write-Host "   Reiniciando todos os serviços..." -ForegroundColor Cyan
                docker-compose restart
            }
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Laboratório reiniciado com sucesso!" -ForegroundColor Green
            }
        }
        
        "clean" {
            Write-Host "🧹 Limpando Laboratório TESTEX..." -ForegroundColor Yellow
            Write-Host "   ⚠️  Isso removerá todos os containers, volumes e dados!" -ForegroundColor Red
            
            $confirmation = Read-Host "   Tem certeza? (digite 'CONFIRMAR' para continuar)"
            
            if ($confirmation -eq "CONFIRMAR") {
                docker-compose down -v --remove-orphans
                docker system prune -f
                Write-Host "✅ Laboratório limpo com sucesso!" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Operação cancelada" -ForegroundColor Yellow
            }
        }
        
        "test" {
            Write-Host "🧪 Testando conectividade do laboratório..." -ForegroundColor Cyan
            
            # Executar script de teste
            $testScript = Join-Path $PSScriptRoot "Test-Laboratory.ps1"
            if (Test-Path $testScript) {
                & $testScript -Detailed
            }
            else {
                Write-Host "❌ Script de teste não encontrado: $testScript" -ForegroundColor Red
            }
        }
        
        "help" {
            Write-Host "🆘 Ajuda do Laboratório TESTEX" -ForegroundColor Cyan
            Write-Host "==============================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Comandos disponíveis:" -ForegroundColor Yellow
            Write-Host "  start    - Inicia o laboratório (todos os serviços ou específico)" -ForegroundColor White
            Write-Host "  stop     - Para o laboratório" -ForegroundColor White
            Write-Host "  status   - Mostra status dos serviços" -ForegroundColor White
            Write-Host "  test     - Testa conectividade de todos os serviços" -ForegroundColor White
            Write-Host "  logs     - Exibe logs dos serviços" -ForegroundColor White
            Write-Host "  restart  - Reinicia os serviços" -ForegroundColor White
            Write-Host "  clean    - Remove todos os containers e dados" -ForegroundColor White
            Write-Host "  help     - Exibe esta ajuda" -ForegroundColor White
            Write-Host ""
            Write-Host "Exemplos:" -ForegroundColor Yellow
            Write-Host "  .\lab.ps1 start                    # Inicia todo o laboratório" -ForegroundColor Gray
            Write-Host "  .\lab.ps1 start -Service sqlserver # Inicia apenas SQL Server" -ForegroundColor Gray
            Write-Host "  .\lab.ps1 status                   # Mostra status dos serviços" -ForegroundColor Gray
            Write-Host "  .\lab.ps1 test                     # Testa conectividade completa" -ForegroundColor Gray
            Write-Host "  .\lab.ps1 logs -Service uma-api    # Logs apenas da API UMA" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Serviços disponíveis:" -ForegroundColor Yellow
            Write-Host "  • sqlserver    - SQL Server Express" -ForegroundColor White
            Write-Host "  • openldap     - OpenLDAP (simulador AD)" -ForegroundColor White
            Write-Host "  • phpldapadmin - Interface web LDAP" -ForegroundColor White
            Write-Host "  • samba        - Servidor de arquivos SMB" -ForegroundColor White
            Write-Host "  • uma-api      - API UMA simulada" -ForegroundColor White
            Write-Host "  • mailhog      - Servidor email de teste" -ForegroundColor White
            Write-Host "  • python-env   - Ambiente Python para testes" -ForegroundColor White
        }
    }
}

# Executar comando se script foi chamado diretamente
if ($MyInvocation.InvocationName -ne '.') {
    if ($args.Count -eq 0) {
        Invoke-LabCommand -Action "help"
    }
    else {
        $action = $args[0]
        $service = if ($args.Count -gt 1) { $args[1] } else { "" }
        
        Invoke-LabCommand -Action $action -Service $service
    }
}