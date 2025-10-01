# TESTEX - Script de Validação do Sistema
# Valida configurações, conectividade e integridade do ambiente

param(
    [string]$ConfigPath = ".\Config\config.json",
    [switch]$Detailed,
    [switch]$TestConnections,
    [string]$LogLevel = "Info"
)

# Importar módulos necessários
$modulePath = Join-Path $PSScriptRoot "..\Modules"
Import-Module (Join-Path $modulePath "LoggingModule.psm1") -Force
Import-Module (Join-Path $modulePath "DatabaseOperations.psm1") -Force
Import-Module (Join-Path $modulePath "ADOperations.psm1") -Force
Import-Module (Join-Path $modulePath "FileOperations.psm1") -Force
Import-Module (Join-Path $modulePath "UMAOperations.psm1") -Force

# Carregar configurações
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Arquivo de configuração não encontrado: $ConfigPath"
    exit 1
}

$config = Get-Content $ConfigPath | ConvertFrom-Json

# Configurar logging
Initialize-Logging -LogPath $config.logging.logPath -LogLevel $LogLevel

Write-Log "=== INICIANDO VALIDAÇÃO DO SISTEMA TESTEX ===" -Level Info

# Resultados da validação
$validationResults = @{
    Configuration = @{ Valid = $false; Issues = @() }
    Modules = @{ Valid = $false; Issues = @() }
    Connections = @{ Valid = $false; Issues = @() }
    FileSystem = @{ Valid = $false; Issues = @() }
    Overall = @{ Valid = $false; Score = 0 }
}

# 1. VALIDAÇÃO DE CONFIGURAÇÃO
Write-Log "--- VALIDANDO CONFIGURAÇÃO ---" -Level Info

try {
    # Validar estrutura de configuração
    $requiredSections = @('database', 'activeDirectory', 'fileSystem', 'uma', 'email', 'jenkins', 'logging')
    $missingSections = @()
    
    foreach ($section in $requiredSections) {
        if (-not $config.PSObject.Properties.Name.Contains($section)) {
            $missingSections += $section
        }
    }
    
    if ($missingSections.Count -eq 0) {
        Write-Log "Todas as seções de configuração estão presentes" -Level Info
        
        # Validar configurações específicas
        $configIssues = @()
        
        # Database
        if (-not $config.database.server -or -not $config.database.database) {
            $configIssues += "Configuração de banco incompleta"
        }
        
        # Active Directory
        if (-not $config.activeDirectory.domain) {
            $configIssues += "Domínio do AD não configurado"
        }
        
        # File System
        if (-not $config.fileSystem.rootPath -or -not $config.fileSystem.backupPath) {
            $configIssues += "Caminhos de arquivos não configurados"
        }
        
        # UMA
        if (-not $config.uma.apiUrl -or -not $config.uma.apiKey) {
            $configIssues += "API do UMA não configurada"
        }
        
        if ($configIssues.Count -eq 0) {
            $validationResults.Configuration.Valid = $true
            Write-Log "Configuração validada com sucesso" -Level Info
        }
        else {
            $validationResults.Configuration.Issues = $configIssues
            Write-Log "Problemas na configuração encontrados: $($configIssues -join ', ')" -Level Warning
        }
    }
    else {
        $validationResults.Configuration.Issues = $missingSections.ForEach({ "Seção ausente: $_" })
        Write-Log "Seções de configuração ausentes: $($missingSections -join ', ')" -Level Error
    }
}
catch {
    $validationResults.Configuration.Issues += "Erro ao validar configuração: $($_.Exception.Message)"
    Write-Log "Erro na validação de configuração: $($_.Exception.Message)" -Level Error
}

# 2. VALIDAÇÃO DE MÓDULOS
Write-Log "--- VALIDANDO MÓDULOS ---" -Level Info

try {
    $moduleFiles = @(
        "LoggingModule.psm1",
        "DatabaseOperations.psm1",
        "ADOperations.psm1",
        "FileOperations.psm1",
        "UMAOperations.psm1"
    )
    
    $missingModules = @()
    $moduleIssues = @()
    
    foreach ($moduleFile in $moduleFiles) {
        $modulePath = Join-Path $PSScriptRoot "..\Modules\$moduleFile"
        
        if (Test-Path $modulePath) {
            try {
                # Tentar importar o módulo para validar sintaxe
                Import-Module $modulePath -Force -ErrorAction Stop
                Write-Log "Módulo $moduleFile validado" -Level Debug
            }
            catch {
                $moduleIssues += "Erro no módulo $moduleFile`: $($_.Exception.Message)"
            }
        }
        else {
            $missingModules += $moduleFile
        }
    }
    
    if ($missingModules.Count -eq 0 -and $moduleIssues.Count -eq 0) {
        $validationResults.Modules.Valid = $true
        Write-Log "Todos os módulos estão presentes e válidos" -Level Info
    }
    else {
        if ($missingModules.Count -gt 0) {
            $validationResults.Modules.Issues += $missingModules.ForEach({ "Módulo ausente: $_" })
        }
        $validationResults.Modules.Issues += $moduleIssues
        Write-Log "Problemas com módulos encontrados" -Level Warning
    }
}
catch {
    $validationResults.Modules.Issues += "Erro ao validar módulos: $($_.Exception.Message)"
    Write-Log "Erro na validação de módulos: $($_.Exception.Message)" -Level Error
}

# 3. VALIDAÇÃO DE CONECTIVIDADE (se solicitado)
if ($TestConnections) {
    Write-Log "--- TESTANDO CONECTIVIDADE ---" -Level Info
    
    $connectionIssues = @()
    
    try {
        # Testar conexão com banco de dados
        Write-Log "Testando conexão com banco de dados..." -Level Info
        $dbConnected = Connect-ToDatabase -Server $config.database.server -Database $config.database.database -UseWindowsAuth:$config.database.useWindowsAuth
        
        if ($dbConnected) {
            Write-Log "Conexão com banco de dados: OK" -Level Info
        }
        else {
            $connectionIssues += "Falha na conexão com banco de dados"
        }
    }
    catch {
        $connectionIssues += "Erro ao conectar com banco: $($_.Exception.Message)"
    }
    
    try {
        # Testar conexão com Active Directory
        Write-Log "Testando conexão com Active Directory..." -Level Info
        $adConnected = Connect-ToActiveDirectory -Domain $config.activeDirectory.domain -Username $config.activeDirectory.username -Password $config.activeDirectory.password
        
        if ($adConnected) {
            Write-Log "Conexão com Active Directory: OK" -Level Info
        }
        else {
            $connectionIssues += "Falha na conexão com Active Directory"
        }
    }
    catch {
        $connectionIssues += "Erro ao conectar com AD: $($_.Exception.Message)"
    }
    
    try {
        # Testar conexão com UMA
        Write-Log "Testando conexão com UMA..." -Level Info
        $umaConnected = Connect-ToUMA -ApiUrl $config.uma.apiUrl -ApiKey $config.uma.apiKey
        
        if ($umaConnected) {
            $umaHealthy = Test-UMAConnectivity
            if ($umaHealthy) {
                Write-Log "Conexão com UMA: OK" -Level Info
            }
            else {
                $connectionIssues += "UMA não está saudável"
            }
        }
        else {
            $connectionIssues += "Falha na conexão com UMA"
        }
    }
    catch {
        $connectionIssues += "Erro ao conectar com UMA: $($_.Exception.Message)"
    }
    
    if ($connectionIssues.Count -eq 0) {
        $validationResults.Connections.Valid = $true
        Write-Log "Todas as conexões estão funcionando" -Level Info
    }
    else {
        $validationResults.Connections.Issues = $connectionIssues
        Write-Log "Problemas de conectividade encontrados" -Level Warning
    }
}

# 4. VALIDAÇÃO DO SISTEMA DE ARQUIVOS
Write-Log "--- VALIDANDO SISTEMA DE ARQUIVOS ---" -Level Info

try {
    $fsIssues = @()
    
    # Verificar caminhos essenciais
    $essentialPaths = @(
        $config.fileSystem.rootPath,
        $config.fileSystem.backupPath,
        $config.fileSystem.archivePath,
        $config.logging.logPath
    )
    
    foreach ($path in $essentialPaths) {
        if ($path -and -not (Test-Path $path)) {
            try {
                New-Item -ItemType Directory -Path $path -Force | Out-Null
                Write-Log "Diretório criado: $path" -Level Info
            }
            catch {
                $fsIssues += "Não foi possível criar diretório: $path"
            }
        }
    }
    
    # Verificar permissões de escrita
    $testFile = Join-Path $config.logging.logPath "test-write.tmp"
    try {
        "test" | Out-File -FilePath $testFile -ErrorAction Stop
        Remove-Item $testFile -ErrorAction SilentlyContinue
        Write-Log "Permissões de escrita: OK" -Level Info
    }
    catch {
        $fsIssues += "Sem permissão de escrita no diretório de logs"
    }
    
    if ($fsIssues.Count -eq 0) {
        $validationResults.FileSystem.Valid = $true
        Write-Log "Sistema de arquivos validado" -Level Info
    }
    else {
        $validationResults.FileSystem.Issues = $fsIssues
        Write-Log "Problemas no sistema de arquivos encontrados" -Level Warning
    }
}
catch {
    $validationResults.FileSystem.Issues += "Erro ao validar sistema de arquivos: $($_.Exception.Message)"
    Write-Log "Erro na validação do sistema de arquivos: $($_.Exception.Message)" -Level Error
}

# CALCULAR SCORE GERAL
$validSections = ($validationResults.Configuration.Valid, $validationResults.Modules.Valid, $validationResults.FileSystem.Valid).Where({ $_ }).Count
$totalSections = 3

if ($TestConnections) {
    $totalSections++
    if ($validationResults.Connections.Valid) {
        $validSections++
    }
}

$validationResults.Overall.Score = [math]::Round(($validSections / $totalSections) * 100)
$validationResults.Overall.Valid = $validationResults.Overall.Score -eq 100

# RELATÓRIO FINAL
Write-Log "=== RELATÓRIO DE VALIDAÇÃO ===" -Level Info
Write-Log "Score Geral: $($validationResults.Overall.Score)%" -Level Info
Write-Log "Configuração: $($validationResults.Configuration.Valid)" -Level Info
Write-Log "Módulos: $($validationResults.Modules.Valid)" -Level Info
Write-Log "Sistema de Arquivos: $($validationResults.FileSystem.Valid)" -Level Info

if ($TestConnections) {
    Write-Log "Conectividade: $($validationResults.Connections.Valid)" -Level Info
}

# Exibir detalhes se solicitado
if ($Detailed) {
    Write-Log "--- DETALHES DOS PROBLEMAS ---" -Level Info
    
    if ($validationResults.Configuration.Issues.Count -gt 0) {
        Write-Log "Problemas de Configuração:" -Level Warning
        foreach ($issue in $validationResults.Configuration.Issues) {
            Write-Log "  - $issue" -Level Warning
        }
    }
    
    if ($validationResults.Modules.Issues.Count -gt 0) {
        Write-Log "Problemas de Módulos:" -Level Warning
        foreach ($issue in $validationResults.Modules.Issues) {
            Write-Log "  - $issue" -Level Warning
        }
    }
    
    if ($validationResults.FileSystem.Issues.Count -gt 0) {
        Write-Log "Problemas de Sistema de Arquivos:" -Level Warning
        foreach ($issue in $validationResults.FileSystem.Issues) {
            Write-Log "  - $issue" -Level Warning
        }
    }
    
    if ($TestConnections -and $validationResults.Connections.Issues.Count -gt 0) {
        Write-Log "Problemas de Conectividade:" -Level Warning
        foreach ($issue in $validationResults.Connections.Issues) {
            Write-Log "  - $issue" -Level Warning
        }
    }
}

# Exportar relatório
$reportFileName = "Validation-Report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$reportPath = Join-Path ".\Reports" $reportFileName

if (-not (Test-Path ".\Reports")) {
    New-Item -ItemType Directory -Path ".\Reports" -Force | Out-Null
}

$validationResults | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportPath -Encoding UTF8
Write-Log "Relatório de validação exportado: $reportPath" -Level Info

Write-Log "=== VALIDAÇÃO CONCLUÍDA ===" -Level Info

# Código de saída baseado no resultado
if ($validationResults.Overall.Valid) {
    exit 0  # Tudo OK
}
elseif ($validationResults.Overall.Score -ge 75) {
    exit 1  # Maioria OK, alguns problemas
}
else {
    exit 2  # Muitos problemas
}