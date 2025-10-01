# Módulo de Logging para TESTEX
# Sistema centralizado de logs

$script:LogPath = ".\Logs"
$script:LogLevel = "INFO"
$script:MaxLogFiles = 10
$script:MaxLogSizeMB = 50

function Initialize-Logging {
    param(
        [string]$LogPath = ".\Logs",
        [string]$LogLevel = "INFO",
        [int]$MaxLogFiles = 10,
        [int]$MaxLogSizeMB = 50
    )
    
    $script:LogPath = $LogPath
    $script:LogLevel = $LogLevel
    $script:MaxLogFiles = $MaxLogFiles
    $script:MaxLogSizeMB = $MaxLogSizeMB
    
    if (-not (Test-Path $LogPath)) {
        New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
    }
    
    # Rotacionar logs antigos se necessário
    Invoke-LogRotation
}

function Write-Log {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")]
        [string]$Level = "INFO",
        [string]$Component = "TESTEX",
        [string]$LogFile = $null
    )
    
    # Verificar se deve logar baseado no nível
    $levelPriority = @{
        "DEBUG" = 0
        "INFO" = 1
        "WARNING" = 2
        "ERROR" = 3
        "CRITICAL" = 4
    }
    
    if ($levelPriority[$Level] -lt $levelPriority[$script:LogLevel]) {
        return
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $processId = $PID
    $threadId = [System.Threading.Thread]::CurrentThread.ManagedThreadId
    
    $logEntry = "[$timestamp] [$Level] [$Component] [PID:$processId] [TID:$threadId] $Message"
    
    # Determinar arquivo de log
    if (-not $LogFile) {
        $LogFile = "TESTEX-$(Get-Date -Format 'yyyyMMdd').log"
    }
    
    $logFilePath = Join-Path $script:LogPath $LogFile
    
    try {
        # Escrever no arquivo
        Add-Content -Path $logFilePath -Value $logEntry -Encoding UTF8
        
        # Também escrever no console se apropriado
        switch ($Level) {
            "DEBUG" { Write-Verbose $logEntry }
            "INFO" { Write-Host $logEntry -ForegroundColor White }
            "WARNING" { Write-Warning $logEntry }
            "ERROR" { Write-Error $logEntry }
            "CRITICAL" { Write-Host $logEntry -ForegroundColor Red -BackgroundColor Yellow }
        }
        
        # Verificar tamanho do arquivo e rotacionar se necessário
        $logFileInfo = Get-Item $logFilePath -ErrorAction SilentlyContinue
        if ($logFileInfo -and ($logFileInfo.Length / 1MB) -gt $script:MaxLogSizeMB) {
            Invoke-LogRotation
        }
    }
    catch {
        Write-Warning "Falha ao escrever log: $($_.Exception.Message)"
    }
}

function Invoke-LogRotation {
    try {
        $logFiles = Get-ChildItem -Path $script:LogPath -Filter "*.log" | 
                   Sort-Object LastWriteTime -Descending
        
        # Remover arquivos excedentes
        if ($logFiles.Count -gt $script:MaxLogFiles) {
            $filesToRemove = $logFiles | Select-Object -Skip $script:MaxLogFiles
            foreach ($file in $filesToRemove) {
                Remove-Item $file.FullName -Force
                Write-Log "Arquivo de log antigo removido: $($file.Name)" -Level INFO -Component "LogRotation"
            }
        }
        
        # Compactar logs antigos (mais de 7 dias)
        $oldLogs = $logFiles | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
        foreach ($oldLog in $oldLogs) {
            $zipPath = $oldLog.FullName + ".zip"
            if (-not (Test-Path $zipPath)) {
                Compress-Archive -Path $oldLog.FullName -DestinationPath $zipPath
                Remove-Item $oldLog.FullName -Force
                Write-Log "Log antigo compactado: $($oldLog.Name)" -Level INFO -Component "LogRotation"
            }
        }
    }
    catch {
        Write-Warning "Erro na rotação de logs: $($_.Exception.Message)"
    }
}

function Get-LogEntries {
    param(
        [string]$LogFile = $null,
        [string]$Level = $null,
        [string]$Component = $null,
        [DateTime]$StartTime = (Get-Date).AddHours(-1),
        [DateTime]$EndTime = (Get-Date),
        [int]$Last = 0
    )
    
    try {
        if ($LogFile) {
            $logFiles = @(Join-Path $script:LogPath $LogFile)
        }
        else {
            $logFiles = Get-ChildItem -Path $script:LogPath -Filter "*.log" | 
                       Select-Object -ExpandProperty FullName
        }
        
        $entries = @()
        
        foreach ($file in $logFiles) {
            if (Test-Path $file) {
                $content = Get-Content $file
                
                foreach ($line in $content) {
                    if ($line -match '^\[([^\]]+)\] \[([^\]]+)\] \[([^\]]+)\] \[PID:(\d+)\] \[TID:(\d+)\] (.+)$') {
                        $logEntry = [PSCustomObject]@{
                            Timestamp = [DateTime]::ParseExact($Matches[1], "yyyy-MM-dd HH:mm:ss.fff", $null)
                            Level = $Matches[2]
                            Component = $Matches[3]
                            ProcessId = [int]$Matches[4]
                            ThreadId = [int]$Matches[5]
                            Message = $Matches[6]
                            File = Split-Path $file -Leaf
                        }
                        
                        # Aplicar filtros
                        if ($Level -and $logEntry.Level -ne $Level) { continue }
                        if ($Component -and $logEntry.Component -ne $Component) { continue }
                        if ($logEntry.Timestamp -lt $StartTime -or $logEntry.Timestamp -gt $EndTime) { continue }
                        
                        $entries += $logEntry
                    }
                }
            }
        }
        
        # Ordenar por timestamp
        $entries = $entries | Sort-Object Timestamp -Descending
        
        # Aplicar limite se especificado
        if ($Last -gt 0) {
            $entries = $entries | Select-Object -First $Last
        }
        
        return $entries
    }
    catch {
        Write-Warning "Erro ao ler logs: $($_.Exception.Message)"
        return @()
    }
}

function Export-LogReport {
    param(
        [string]$OutputPath = ".\Reports",
        [DateTime]$StartTime = (Get-Date).AddDays(-1),
        [DateTime]$EndTime = (Get-Date),
        [string]$Format = "JSON"
    )
    
    try {
        $entries = Get-LogEntries -StartTime $StartTime -EndTime $EndTime
        
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        
        switch ($Format.ToUpper()) {
            "JSON" {
                $fileName = "LogReport-$timestamp.json"
                $filePath = Join-Path $OutputPath $fileName
                $entries | ConvertTo-Json -Depth 3 | Out-File -FilePath $filePath -Encoding UTF8
            }
            "CSV" {
                $fileName = "LogReport-$timestamp.csv"
                $filePath = Join-Path $OutputPath $fileName
                $entries | Export-Csv -Path $filePath -NoTypeInformation -Encoding UTF8
            }
            "HTML" {
                $fileName = "LogReport-$timestamp.html"
                $filePath = Join-Path $OutputPath $fileName
                $html = ConvertTo-LogHtml -Entries $entries
                $html | Out-File -FilePath $filePath -Encoding UTF8
            }
        }
        
        Write-Log "Relatório de logs exportado: $filePath" -Level INFO -Component "LogReport"
        return $filePath
    }
    catch {
        Write-Log "Erro ao exportar relatório de logs: $($_.Exception.Message)" -Level ERROR -Component "LogReport"
        throw
    }
}

function ConvertTo-LogHtml {
    param([array]$Entries)
    
    $html = @"
<!DOCTYPE html>
<html>
<head>
    <title>TESTEX - Relatório de Logs</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .ERROR { background-color: #ffebee; }
        .WARNING { background-color: #fff3e0; }
        .CRITICAL { background-color: #ffcdd2; }
    </style>
</head>
<body>
    <h1>TESTEX - Relatório de Logs</h1>
    <p>Gerado em: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
    <table>
        <tr>
            <th>Timestamp</th>
            <th>Level</th>
            <th>Component</th>
            <th>Message</th>
            <th>File</th>
        </tr>
"@
    
    foreach ($entry in $Entries) {
        $cssClass = if ($entry.Level -in @("ERROR", "WARNING", "CRITICAL")) { $entry.Level } else { "" }
        $html += @"
        <tr class="$cssClass">
            <td>$($entry.Timestamp.ToString("yyyy-MM-dd HH:mm:ss.fff"))</td>
            <td>$($entry.Level)</td>
            <td>$($entry.Component)</td>
            <td>$([System.Web.HttpUtility]::HtmlEncode($entry.Message))</td>
            <td>$($entry.File)</td>
        </tr>
"@
    }
    
    $html += @"
    </table>
</body>
</html>
"@
    
    return $html
}

function Clear-Logs {
    param(
        [int]$OlderThanDays = 30,
        [switch]$Force
    )
    
    try {
        $cutoffDate = (Get-Date).AddDays(-$OlderThanDays)
        $oldLogs = Get-ChildItem -Path $script:LogPath -Filter "*.log" | 
                  Where-Object { $_.LastWriteTime -lt $cutoffDate }
        
        if ($oldLogs.Count -eq 0) {
            Write-Log "Nenhum log antigo encontrado para limpeza" -Level INFO -Component "LogCleanup"
            return
        }
        
        if (-not $Force) {
            $response = Read-Host "Remover $($oldLogs.Count) arquivos de log mais antigos que $OlderThanDays dias? (s/n)"
            if ($response -ne 's' -and $response -ne 'S') {
                return
            }
        }
        
        foreach ($log in $oldLogs) {
            Remove-Item $log.FullName -Force
            Write-Log "Log removido: $($log.Name)" -Level INFO -Component "LogCleanup"
        }
        
        Write-Log "Limpeza de logs concluída: $($oldLogs.Count) arquivos removidos" -Level INFO -Component "LogCleanup"
    }
    catch {
        Write-Log "Erro na limpeza de logs: $($_.Exception.Message)" -Level ERROR -Component "LogCleanup"
        throw
    }
}

# Inicializar logging ao carregar o módulo
Initialize-Logging

Export-ModuleMember -Function *