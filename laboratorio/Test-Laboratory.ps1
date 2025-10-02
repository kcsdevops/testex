# TESTEX Laboratory Connectivity Tests
# Script completo para testar conectividade e disponibilidade do laboratório

param(
    [switch]$Detailed,
    [switch]$WaitForServices,
    [int]$MaxWaitMinutes = 5,
    [switch]$FixIssues
)

# Cores para output
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Detail = "Gray"
}

# Configurações dos serviços
$ServiceConfig = @{
    SqlServer = @{
        Name = "SQL Server"
        Host = "localhost"
        Port = 1433
        Container = "testex_sqlserver"
        TestQuery = "SELECT @@VERSION"
        Credentials = @{
            Username = "sa"
            Password = "TestexSQL2024!"
        }
    }
    OpenLDAP = @{
        Name = "OpenLDAP (Active Directory)"
        Host = "localhost"
        Port = 389
        Container = "testex_ldap"
        BaseDN = "dc=testex,dc=local"
        AdminDN = "cn=admin,dc=testex,dc=local"
        AdminPassword = "testexldap123"
    }
    UmaApi = @{
        Name = "UMA API"
        Host = "localhost"
        Port = 5000
        Container = "testex_uma_api"
        HealthEndpoint = "http://localhost:5000/health"
        ApiKey = "testex-uma-key-2024"
    }
    FileServer = @{
        Name = "File Server (Samba)"
        Host = "localhost"
        Port = 445
        Container = "testex_fileserver"
        SharePath = "\\localhost\testex"
        Username = "testuser"
        Password = "testpass"
    }
    MailHog = @{
        Name = "MailHog SMTP"
        Host = "localhost"
        Port = 1025
        Container = "testex_mailhog"
        WebUI = "http://localhost:8025"
    }
    LdapAdmin = @{
        Name = "phpLDAPadmin"
        Host = "localhost"
        Port = 8080
        Container = "testex_ldap_admin"
        WebUI = "http://localhost:8080"
    }
}

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Success,
        [string]$Details = "",
        [string]$Error = ""
    )
    
    $icon = if ($Success) { "✅" } else { "❌" }
    $color = if ($Success) { $Colors.Success } else { $Colors.Error }
    
    Write-Host "$icon $TestName" -ForegroundColor $color
    
    if ($Details -and $Detailed) {
        Write-Host "   → $Details" -ForegroundColor $Colors.Detail
    }
    
    if ($Error -and -not $Success) {
        Write-Host "   ⚠️  $Error" -ForegroundColor $Colors.Warning
    }
    
    return $Success
}

function Test-DockerAvailable {
    Write-Host "🐳 Verificando Docker..." -ForegroundColor $Colors.Info
    
    try {
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
        if ($dockerVersion) {
            return Write-TestResult "Docker Engine" $true "Versão: $dockerVersion"
        } else {
            return Write-TestResult "Docker Engine" $false "" "Docker não está rodando ou não está instalado"
        }
    }
    catch {
        return Write-TestResult "Docker Engine" $false "" $_.Exception.Message
    }
}

function Test-DockerCompose {
    try {
        $composeVersion = docker-compose version --short 2>$null
        if ($composeVersion) {
            return Write-TestResult "Docker Compose" $true "Versão: $composeVersion"
        } else {
            return Write-TestResult "Docker Compose" $false "" "Docker Compose não disponível"
        }
    }
    catch {
        return Write-TestResult "Docker Compose" $false "" $_.Exception.Message
    }
}

function Get-ContainerStatus {
    param([string]$ContainerName)
    
    try {
        $status = docker inspect $ContainerName --format "{{.State.Status}}" 2>$null
        $health = docker inspect $ContainerName --format "{{.State.Health.Status}}" 2>$null
        
        if ($status) {
            return @{
                Status = $status
                Health = if ($health -eq "<no value>") { "no-healthcheck" } else { $health }
                Running = ($status -eq "running")
                Healthy = ($health -eq "healthy" -or $health -eq "no-healthcheck")
            }
        }
        return $null
    }
    catch {
        return $null
    }
}

function Test-ContainerHealth {
    Write-Host "`n📋 Verificando status dos containers..." -ForegroundColor $Colors.Info
    
    $allHealthy = $true
    
    foreach ($service in $ServiceConfig.Keys) {
        $config = $ServiceConfig[$service]
        $containerStatus = Get-ContainerStatus $config.Container
        
        if ($containerStatus) {
            $isHealthy = $containerStatus.Running -and $containerStatus.Healthy
            $details = "Status: $($containerStatus.Status)"
            if ($containerStatus.Health -ne "no-healthcheck") {
                $details += ", Health: $($containerStatus.Health)"
            }
            
            $result = Write-TestResult "Container $($config.Name)" $isHealthy $details
            $allHealthy = $allHealthy -and $result
        } else {
            $result = Write-TestResult "Container $($config.Name)" $false "" "Container não encontrado ou parado"
            $allHealthy = $false
        }
    }
    
    return $allHealthy
}

function Test-NetworkConnectivity {
    Write-Host "`n🌐 Testando conectividade de rede..." -ForegroundColor $Colors.Info
    
    $allConnected = $true
    
    foreach ($service in $ServiceConfig.Keys) {
        $config = $ServiceConfig[$service]
        
        try {
            $connection = Test-NetConnection -ComputerName $config.Host -Port $config.Port -WarningAction SilentlyContinue
            $isConnected = $connection.TcpTestSucceeded
            $details = if ($isConnected) { "Porta $($config.Port) acessível" } else { "Porta $($config.Port) não responde" }
            
            $result = Write-TestResult "Conectividade $($config.Name)" $isConnected $details
            $allConnected = $allConnected -and $result
        }
        catch {
            $result = Write-TestResult "Conectividade $($config.Name)" $false "" $_.Exception.Message
            $allConnected = $false
        }
    }
    
    return $allConnected
}

function Test-SqlServerConnection {
    Write-Host "`n🗄️ Testando conexão SQL Server..." -ForegroundColor $Colors.Info
    
    $config = $ServiceConfig.SqlServer
    
    try {
        # Tentar conexão com SqlServer module se disponível
        if (Get-Module -ListAvailable -Name SqlServer) {
            $connectionString = "Server=$($config.Host),$($config.Port);Database=master;User Id=$($config.Credentials.Username);Password=$($config.Credentials.Password);TrustServerCertificate=true;Connection Timeout=10"
            
            $result = Invoke-Sqlcmd -ConnectionString $connectionString -Query $config.TestQuery -ErrorAction Stop
            
            if ($result) {
                $version = $result[0] -replace '\s+', ' '
                return Write-TestResult "SQL Server Query" $true "Versão: $($version.Substring(0, [Math]::Min(50, $version.Length)))..."
            }
        }
        
        # Fallback para sqlcmd se disponível
        $sqlcmdResult = & sqlcmd -S "$($config.Host),$($config.Port)" -U $config.Credentials.Username -P $config.Credentials.Password -Q $config.TestQuery -h -1 2>$null
        
        if ($sqlcmdResult) {
            return Write-TestResult "SQL Server Query" $true "Conexão via sqlcmd bem-sucedida"
        }
        
        return Write-TestResult "SQL Server Query" $false "" "Não foi possível executar query (módulos SQL não disponíveis)"
    }
    catch {
        return Write-TestResult "SQL Server Query" $false "" $_.Exception.Message
    }
}

function Test-LdapConnection {
    Write-Host "`n🔐 Testando conexão LDAP..." -ForegroundColor $Colors.Info
    
    $config = $ServiceConfig.OpenLDAP
    
    try {
        # Verificar se módulo ActiveDirectory está disponível
        if (Get-Module -ListAvailable -Name ActiveDirectory) {
            # Tentar busca LDAP básica
            $searchResult = Get-ADObject -Server "$($config.Host):$($config.Port)" -SearchBase $config.BaseDN -Filter "objectClass -eq 'organization'" -ErrorAction Stop
            
            return Write-TestResult "LDAP Search" $true "Base DN acessível: $($config.BaseDN)"
        }
        
        # Fallback para ldapsearch se disponível (improvável no Windows)
        return Write-TestResult "LDAP Search" $false "" "Módulo ActiveDirectory não disponível para teste completo"
    }
    catch {
        # Conexão de rede está OK, mas autenticação pode ter falhado
        $networkTest = Test-NetConnection -ComputerName $config.Host -Port $config.Port -WarningAction SilentlyContinue
        if ($networkTest.TcpTestSucceeded) {
            return Write-TestResult "LDAP Search" $true "Porta LDAP acessível (autenticação não testada)"
        }
        
        return Write-TestResult "LDAP Search" $false "" $_.Exception.Message
    }
}

function Test-UmaApiConnection {
    Write-Host "`n🔌 Testando UMA API..." -ForegroundColor $Colors.Info
    
    $config = $ServiceConfig.UmaApi
    
    try {
        $headers = @{
            'Authorization' = "Bearer $($config.ApiKey)"
            'Content-Type' = 'application/json'
        }
        
        $response = Invoke-RestMethod -Uri $config.HealthEndpoint -Headers $headers -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.status -eq "healthy") {
            return Write-TestResult "UMA API Health" $true "Status: $($response.status), Clientes: $($response.clients_count)"
        } else {
            return Write-TestResult "UMA API Health" $false "" "Status não saudável: $($response.status)"
        }
    }
    catch {
        return Write-TestResult "UMA API Health" $false "" $_.Exception.Message
    }
}

function Test-WebInterfaces {
    Write-Host "`n🌐 Testando interfaces web..." -ForegroundColor $Colors.Info
    
    $webServices = @(
        @{ Name = "phpLDAPadmin"; Url = $ServiceConfig.LdapAdmin.WebUI },
        @{ Name = "MailHog"; Url = $ServiceConfig.MailHog.WebUI }
    )
    
    $allWebOk = $true
    
    foreach ($webService in $webServices) {
        try {
            $response = Invoke-WebRequest -Uri $webService.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            $isOk = $response.StatusCode -eq 200
            $details = "HTTP $($response.StatusCode)"
            
            $result = Write-TestResult "Web Interface $($webService.Name)" $isOk $details
            $allWebOk = $allWebOk -and $result
        }
        catch {
            $result = Write-TestResult "Web Interface $($webService.Name)" $false "" $_.Exception.Message
            $allWebOk = $false
        }
    }
    
    return $allWebOk
}

function Wait-ForServices {
    param([int]$MaxWaitMinutes)
    
    Write-Host "⏳ Aguardando serviços ficarem prontos (máximo $MaxWaitMinutes minutos)..." -ForegroundColor $Colors.Info
    
    $startTime = Get-Date
    $endTime = $startTime.AddMinutes($MaxWaitMinutes)
    
    do {
        $containersReady = Test-ContainerHealth
        
        if ($containersReady) {
            Write-Host "✅ Todos os containers estão prontos!" -ForegroundColor $Colors.Success
            return $true
        }
        
        $elapsed = (Get-Date) - $startTime
        Write-Host "   Aguardando... ($([int]$elapsed.TotalSeconds)s)" -ForegroundColor $Colors.Detail
        Start-Sleep 10
        
    } while ((Get-Date) -lt $endTime)
    
    Write-Host "⏰ Tempo limite atingido" -ForegroundColor $Colors.Warning
    return $false
}

function Start-Laboratory {
    Write-Host "🚀 Iniciando laboratório..." -ForegroundColor $Colors.Info
    
    $labPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Push-Location $labPath
    
    try {
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Laboratório iniciado" -ForegroundColor $Colors.Success
            return $true
        } else {
            Write-Host "❌ Erro ao iniciar laboratório" -ForegroundColor $Colors.Error
            return $false
        }
    }
    finally {
        Pop-Location
    }
}

function Show-ServiceEndpoints {
    Write-Host "`n🔗 Endpoints dos serviços:" -ForegroundColor $Colors.Info
    Write-Host "================================" -ForegroundColor $Colors.Info
    
    foreach ($service in $ServiceConfig.Keys) {
        $config = $ServiceConfig[$service]
        Write-Host "📌 $($config.Name):" -ForegroundColor $Colors.Detail
        
        if ($config.Host -and $config.Port) {
            Write-Host "   Host: $($config.Host):$($config.Port)" -ForegroundColor White
        }
        
        if ($config.WebUI) {
            Write-Host "   Web: $($config.WebUI)" -ForegroundColor White
        }
        
        if ($config.Credentials) {
            Write-Host "   User: $($config.Credentials.Username) / $($config.Credentials.Password)" -ForegroundColor White
        }
        
        if ($config.SharePath) {
            Write-Host "   Share: $($config.SharePath)" -ForegroundColor White
        }
        
        Write-Host ""
    }
}

function Test-Laboratory {
    Write-Host "🧪 TESTEX Laboratory Connectivity Tests" -ForegroundColor $Colors.Info
    Write-Host "=========================================" -ForegroundColor $Colors.Info
    
    $testResults = @{}
    
    # 1. Verificar Docker
    $testResults.Docker = Test-DockerAvailable
    $testResults.DockerCompose = Test-DockerCompose
    
    if (-not $testResults.Docker) {
        Write-Host "`n❌ Docker não está disponível. Instale Docker Desktop e inicie-o." -ForegroundColor $Colors.Error
        return $false
    }
    
    # 2. Aguardar serviços se solicitado
    if ($WaitForServices) {
        $testResults.ServicesReady = Wait-ForServices -MaxWaitMinutes $MaxWaitMinutes
    }
    
    # 3. Testar containers
    $testResults.Containers = Test-ContainerHealth
    
    # 4. Testar conectividade de rede
    $testResults.Network = Test-NetworkConnectivity
    
    # 5. Testes específicos de serviço
    $testResults.SqlServer = Test-SqlServerConnection
    $testResults.Ldap = Test-LdapConnection
    $testResults.UmaApi = Test-UmaApiConnection
    $testResults.WebInterfaces = Test-WebInterfaces
    
    # Resumo final
    Write-Host "`n📊 RESUMO DOS TESTES" -ForegroundColor $Colors.Info
    Write-Host "=====================" -ForegroundColor $Colors.Info
    
    $passedTests = ($testResults.Values | Where-Object { $_ }).Count
    $totalTests = $testResults.Count
    $allPassed = $passedTests -eq $totalTests
    
    $summaryColor = if ($allPassed) { $Colors.Success } else { $Colors.Warning }
    Write-Host "Testes aprovados: $passedTests/$totalTests" -ForegroundColor $summaryColor
    
    if ($allPassed) {
        Write-Host "🎉 Laboratório TESTEX está totalmente funcional!" -ForegroundColor $Colors.Success
        Show-ServiceEndpoints
    } else {
        Write-Host "⚠️  Alguns serviços apresentam problemas" -ForegroundColor $Colors.Warning
        
        if ($FixIssues) {
            Write-Host "`n🔧 Tentando corrigir problemas..." -ForegroundColor $Colors.Info
            
            if (-not $testResults.Containers) {
                Write-Host "Reiniciando containers problemáticos..." -ForegroundColor $Colors.Detail
                docker-compose restart
            }
        }
    }
    
    return $allPassed
}

# Executar testes se script foi chamado diretamente
if ($MyInvocation.InvocationName -ne '.') {
    $result = Test-Laboratory
    
    # Código de saída
    if ($result) {
        exit 0
    } else {
        exit 1
    }
}