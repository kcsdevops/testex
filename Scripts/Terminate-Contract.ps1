# TESTEX - Sistema de Terminação de Contratos
# Script principal para execução das operações de término

param(
    [Parameter(Mandatory)]
    [string]$ClienteId,
    [string]$ConfigPath = ".\Config\config.json",
    [switch]$WhatIf,
    [switch]$NoBackup,
    [switch]$Force,
    [ValidateSet("All", "Database", "AD", "Files", "UMA")]
    [string]$Operation = "All",
    [string]$LogLevel = "Info"
)

# Carregar configurações
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Arquivo de configuração não encontrado: $ConfigPath"
    exit 1
}

$config = Get-Content $ConfigPath | ConvertFrom-Json

# Importar módulos necessários
$modulePath = Join-Path $PSScriptRoot "..\Modules"
Import-Module (Join-Path $modulePath "LoggingModule.psm1") -Force
Import-Module (Join-Path $modulePath "DatabaseOperations.psm1") -Force
Import-Module (Join-Path $modulePath "ADOperations.psm1") -Force
Import-Module (Join-Path $modulePath "FileOperations.psm1") -Force
Import-Module (Join-Path $modulePath "UMAOperations.psm1") -Force

# Configurar logging
Initialize-Logging -LogPath $config.logging.logPath -LogLevel $LogLevel

Write-Log "=== INICIANDO PROCESSO DE TERMINAÇÃO DE CONTRATO ===" -Level Info
Write-Log "Cliente: $ClienteId" -Level Info
Write-Log "Operação: $Operation" -Level Info
Write-Log "Modo de simulação: $($WhatIf.IsPresent)" -Level Info

# Contadores de resultado
$results = @{
    Database = @{ Success = $false; Details = "" }
    AD = @{ Success = $false; Details = "" }
    Files = @{ Success = $false; Details = "" }
    UMA = @{ Success = $false; Details = "" }
    Errors = @()
    StartTime = Get-Date
}

try {
    # 1. OPERAÇÕES DE BANCO DE DADOS
    if ($Operation -eq "All" -or $Operation -eq "Database") {
        Write-Log "--- INICIANDO OPERAÇÕES DE BANCO DE DADOS ---" -Level Info
        
        try {
            # Conectar ao banco
            $dbConnected = Connect-ToDatabase -Server $config.database.server -Database $config.database.database -UseWindowsAuth:$config.database.useWindowsAuth
            
            if ($dbConnected) {
                # Obter informações do cliente
                $clienteInfo = Get-ClienteInfo -ClienteId $ClienteId
                
                if ($clienteInfo) {
                    Write-Log "Cliente encontrado: $($clienteInfo.Nome)" -Level Info
                    
                    # Fazer backup se solicitado
                    if (-not $NoBackup) {
                        $backupPath = Backup-Database -BackupPath $config.database.backupPath -ClienteId $ClienteId -WhatIf:$WhatIf
                        Write-Log "Backup realizado: $backupPath" -Level Info
                    }
                    
                    # Atualizar status do cliente
                    $statusUpdated = Update-ClienteStatus -ClienteId $ClienteId -NovoStatus "TERMINATED" -WhatIf:$WhatIf
                    
                    if ($statusUpdated) {
                        $results.Database.Success = $true
                        $results.Database.Details = "Status atualizado para TERMINATED"
                        Write-Log "Operações de banco concluídas com sucesso" -Level Info
                    }
                }
                else {
                    throw "Cliente não encontrado no banco de dados"
                }
            }
            else {
                throw "Falha na conexão com o banco de dados"
            }
        }
        catch {
            $results.Errors += "Database: $($_.Exception.Message)"
            Write-Log "Erro nas operações de banco: $($_.Exception.Message)" -Level Error
        }
    }
    
    # 2. OPERAÇÕES DO ACTIVE DIRECTORY
    if ($Operation -eq "All" -or $Operation -eq "AD") {
        Write-Log "--- INICIANDO OPERAÇÕES DO ACTIVE DIRECTORY ---" -Level Info
        
        try {
            # Conectar ao AD
            $adConnected = Connect-ToActiveDirectory -Domain $config.activeDirectory.domain -Username $config.activeDirectory.username -Password $config.activeDirectory.password
            
            if ($adConnected) {
                # Buscar usuários do cliente
                $users = Get-ADUsersByClient -ClienteId $ClienteId
                Write-Log "Encontrados $($users.Count) usuários para o cliente" -Level Info
                
                # Buscar grupos do cliente
                $groups = Get-ADGroupsByClient -ClienteId $ClienteId
                Write-Log "Encontrados $($groups.Count) grupos para o cliente" -Level Info
                
                if ($users.Count -gt 0 -or $groups.Count -gt 0) {
                    # Remover usuários
                    if ($users.Count -gt 0) {
                        Remove-ADUsersByClient -ClienteId $ClienteId -WhatIf:$WhatIf -Force:$Force
                    }
                    
                    # Remover grupos
                    if ($groups.Count -gt 0) {
                        Remove-ADGroupsByClient -ClienteId $ClienteId -WhatIf:$WhatIf -Force:$Force
                    }
                    
                    $results.AD.Success = $true
                    $results.AD.Details = "Removidos $($users.Count) usuários e $($groups.Count) grupos"
                    Write-Log "Operações do AD concluídas com sucesso" -Level Info
                }
                else {
                    $results.AD.Success = $true
                    $results.AD.Details = "Nenhum usuário ou grupo encontrado"
                    Write-Log "Nenhum objeto do AD encontrado para remoção" -Level Info
                }
            }
            else {
                throw "Falha na conexão com o Active Directory"
            }
        }
        catch {
            $results.Errors += "AD: $($_.Exception.Message)"
            Write-Log "Erro nas operações do AD: $($_.Exception.Message)" -Level Error
        }
    }
    
    # 3. OPERAÇÕES DE ARQUIVOS
    if ($Operation -eq "All" -or $Operation -eq "Files") {
        Write-Log "--- INICIANDO OPERAÇÕES DE ARQUIVOS ---" -Level Info
        
        try {
            # Buscar arquivos do cliente
            $files = Get-ClienteFiles -ClienteId $ClienteId -SearchPath $config.fileSystem.rootPath
            Write-Log "Encontrados $($files.Count) arquivos para o cliente" -Level Info
            
            if ($files.Count -gt 0) {
                # Fazer backup dos arquivos se solicitado
                if (-not $NoBackup) {
                    $backupResult = Backup-ClienteFiles -ClienteId $ClienteId -Files $files -BackupPath $config.fileSystem.backupPath -WhatIf:$WhatIf
                    Write-Log "Backup de arquivos concluído: $($backupResult.BackupPath)" -Level Info
                }
                
                # Remover arquivos
                $removeResult = Remove-ClienteFiles -ClienteId $ClienteId -Files $files -WhatIf:$WhatIf -Force:$Force
                
                # Comprimir arquivos remanescentes se houver
                if ($removeResult.RemainingFiles.Count -gt 0) {
                    $compressResult = Compress-ClienteFiles -ClienteId $ClienteId -Files $removeResult.RemainingFiles -ArchivePath $config.fileSystem.archivePath -WhatIf:$WhatIf
                    Write-Log "Arquivos comprimidos: $($compressResult.ArchivePath)" -Level Info
                }
                
                $results.Files.Success = $true
                $results.Files.Details = "Processados $($files.Count) arquivos"
                Write-Log "Operações de arquivos concluídas com sucesso" -Level Info
            }
            else {
                $results.Files.Success = $true
                $results.Files.Details = "Nenhum arquivo encontrado"
                Write-Log "Nenhum arquivo encontrado para processamento" -Level Info
            }
        }
        catch {
            $results.Errors += "Files: $($_.Exception.Message)"
            Write-Log "Erro nas operações de arquivos: $($_.Exception.Message)" -Level Error
        }
    }
    
    # 4. OPERAÇÕES DO UMA
    if ($Operation -eq "All" -or $Operation -eq "UMA") {
        Write-Log "--- INICIANDO OPERAÇÕES DO UMA ---" -Level Info
        
        try {
            # Conectar ao UMA
            $umaConnected = Connect-ToUMA -ApiUrl $config.uma.apiUrl -ApiKey $config.uma.apiKey
            
            if ($umaConnected) {
                # Obter informações do cliente no UMA
                $umaClientInfo = Get-UMAClientInfo -ClienteId $ClienteId
                
                if ($umaClientInfo) {
                    Write-Log "Cliente encontrado no UMA: $($umaClientInfo.Nome)" -Level Info
                    
                    # Remover serviços do cliente
                    $removedServices = Remove-UMAClientServices -ClienteId $ClienteId -WhatIf:$WhatIf
                    Write-Log "Serviços removidos: $($removedServices.Count)" -Level Info
                    
                    # Desabilitar cliente
                    $clientDisabled = Disable-UMAClient -ClienteId $ClienteId -Motivo "Terminação de contrato" -WhatIf:$WhatIf
                    
                    # Executar purge se forçado
                    $purgeResult = $null
                    if ($Force) {
                        $purgeResult = Invoke-UMAClientPurge -ClienteId $ClienteId -Force -WhatIf:$WhatIf
                        Write-Log "Purge iniciado: $($purgeResult.PurgeId)" -Level Info
                    }
                    
                    # Exportar relatório
                    $reportPath = Export-UMACleanupReport -ClienteId $ClienteId -PurgeId $purgeResult.PurgeId -RemovedServices $removedServices
                    
                    $results.UMA.Success = $true
                    $results.UMA.Details = "Cliente desabilitado, $($removedServices.Count) serviços removidos"
                    Write-Log "Operações do UMA concluídas com sucesso" -Level Info
                }
                else {
                    $results.UMA.Success = $true
                    $results.UMA.Details = "Cliente não encontrado no UMA"
                    Write-Log "Cliente não encontrado no UMA" -Level Warning
                }
            }
            else {
                throw "Falha na conexão com o UMA"
            }
        }
        catch {
            $results.Errors += "UMA: $($_.Exception.Message)"
            Write-Log "Erro nas operações do UMA: $($_.Exception.Message)" -Level Error
        }
    }
}
catch {
    $results.Errors += "General: $($_.Exception.Message)"
    Write-Log "Erro geral no processo: $($_.Exception.Message)" -Level Error
}
finally {
    $results.EndTime = Get-Date
    $results.Duration = $results.EndTime - $results.StartTime
    
    # Gerar relatório final
    Write-Log "=== RELATÓRIO FINAL ===" -Level Info
    Write-Log "Duração total: $($results.Duration.ToString('hh\:mm\:ss'))" -Level Info
    Write-Log "Database: $($results.Database.Success) - $($results.Database.Details)" -Level Info
    Write-Log "AD: $($results.AD.Success) - $($results.AD.Details)" -Level Info
    Write-Log "Files: $($results.Files.Success) - $($results.Files.Details)" -Level Info
    Write-Log "UMA: $($results.UMA.Success) - $($results.UMA.Details)" -Level Info
    
    if ($results.Errors.Count -gt 0) {
        Write-Log "ERROS ENCONTRADOS:" -Level Error
        foreach ($error in $results.Errors) {
            Write-Log "  - $error" -Level Error
        }
    }
    
    # Exportar relatório JSON
    $reportFileName = "Termination-Report-$ClienteId-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    $reportPath = Join-Path ".\Reports" $reportFileName
    
    if (-not (Test-Path ".\Reports")) {
        New-Item -ItemType Directory -Path ".\Reports" -Force | Out-Null
    }
    
    $results | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Log "Relatório final exportado: $reportPath" -Level Info
    
    Write-Log "=== PROCESSO CONCLUÍDO ===" -Level Info
}

# Retornar código de saída baseado nos resultados
$successCount = ($results.Database.Success, $results.AD.Success, $results.Files.Success, $results.UMA.Success | Where-Object { $_ }).Count
$totalOperations = if ($Operation -eq "All") { 4 } else { 1 }

if ($results.Errors.Count -eq 0 -and $successCount -eq $totalOperations) {
    exit 0  # Sucesso total
}
elseif ($successCount -gt 0) {
    exit 1  # Sucesso parcial
}
else {
    exit 2  # Falha total
}