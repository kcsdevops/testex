# Módulo de Operações de Arquivos
# Funções para gerenciar arquivos .pr4 e outros

function Get-ClienteFiles {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [string]$BasePath = "\\servidor\arquivos\pr4",
        [string]$FilePattern = "*.pr4"
    )
    
    try {
        $searchPattern = "*$ClienteId*$FilePattern"
        $files = Get-ChildItem -Path $BasePath -Filter $searchPattern -Recurse -File
        
        Write-Log "Encontrados $($files.Count) arquivos para o cliente $ClienteId" -Level Info
        
        $fileInfo = @()
        foreach ($file in $files) {
            $fileInfo += [PSCustomObject]@{
                FullName = $file.FullName
                Name = $file.Name
                Size = $file.Length
                LastWriteTime = $file.LastWriteTime
                Directory = $file.Directory.FullName
            }
        }
        
        return $fileInfo
    }
    catch {
        Write-Log "Erro ao buscar arquivos: $($_.Exception.Message)" -Level Error
        return @()
    }
}

function Backup-ClienteFiles {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [string]$BackupPath = "\\servidor\backup",
        [switch]$WhatIf
    )
    
    try {
        $files = Get-ClienteFiles -ClienteId $ClienteId
        
        if ($files.Count -eq 0) {
            Write-Log "Nenhum arquivo encontrado para backup do cliente $ClienteId" -Level Warning
            return @()
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $clientBackupPath = Join-Path $BackupPath "Cliente_$ClienteId_$timestamp"
        
        if (-not $WhatIf) {
            if (-not (Test-Path $clientBackupPath)) {
                New-Item -ItemType Directory -Path $clientBackupPath -Force | Out-Null
            }
        }
        
        $backedUpFiles = @()
        
        foreach ($file in $files) {
            $destinationPath = Join-Path $clientBackupPath $file.Name
            
            if ($WhatIf) {
                Write-Log "SIMULAÇÃO: Faria backup de $($file.FullName) para $destinationPath" -Level Info
            }
            else {
                Copy-Item -Path $file.FullName -Destination $destinationPath -Force
                Write-Log "Backup criado: $destinationPath" -Level Info
            }
            
            $backedUpFiles += $destinationPath
        }
        
        Write-Log "Backup de $($files.Count) arquivos concluído para $clientBackupPath" -Level Info
        return $backedUpFiles
    }
    catch {
        Write-Log "Erro ao fazer backup dos arquivos: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Remove-ClienteFiles {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [switch]$WhatIf,
        [switch]$Force
    )
    
    try {
        $files = Get-ClienteFiles -ClienteId $ClienteId
        
        if ($files.Count -eq 0) {
            Write-Log "Nenhum arquivo encontrado para remoção do cliente $ClienteId" -Level Warning
            return @()
        }
        
        $removedFiles = @()
        
        foreach ($file in $files) {
            if ($WhatIf) {
                Write-Log "SIMULAÇÃO: Removeria arquivo $($file.FullName)" -Level Info
            }
            else {
                if ($Force) {
                    Remove-Item -Path $file.FullName -Force
                }
                else {
                    Remove-Item -Path $file.FullName
                }
                
                Write-Log "Arquivo removido: $($file.FullName)" -Level Info
            }
            
            $removedFiles += $file.FullName
        }
        
        Write-Log "Remoção de $($files.Count) arquivos concluída" -Level Info
        return $removedFiles
    }
    catch {
        Write-Log "Erro ao remover arquivos: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Test-FileSystemAccess {
    param(
        [string]$Path = "\\servidor\arquivos\pr4"
    )
    
    try {
        if (Test-Path $Path) {
            # Tentar criar um arquivo temporário para testar escrita
            $testFile = Join-Path $Path "test_access_$(Get-Date -Format 'yyyyMMddHHmmss').tmp"
            
            "test" | Out-File -FilePath $testFile -Encoding ASCII
            
            if (Test-Path $testFile) {
                Remove-Item $testFile -Force
                Write-Log "Acesso de leitura/escrita confirmado para: $Path" -Level Info
                return $true
            }
        }
        
        Write-Log "Falha no acesso ao sistema de arquivos: $Path" -Level Error
        return $false
    }
    catch {
        Write-Log "Erro ao testar acesso ao sistema de arquivos: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Get-DirectorySize {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )
    
    try {
        if (-not (Test-Path $Path)) {
            return 0
        }
        
        $files = Get-ChildItem -Path $Path -Recurse -File
        $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
        
        return $totalSize
    }
    catch {
        Write-Log "Erro ao calcular tamanho do diretório: $($_.Exception.Message)" -Level Error
        return 0
    }
}

function Export-FileCleanupReport {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [array]$BackedUpFiles,
        [array]$RemovedFiles,
        [string]$OutputPath = ".\Reports"
    )
    
    try {
        $reportData = @{
            ClienteId = $ClienteId
            DateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            BackedUpFiles = $BackedUpFiles
            RemovedFiles = $RemovedFiles
            TotalBackedUp = $BackedUpFiles.Count
            TotalRemoved = $RemovedFiles.Count
            BackupSizeBytes = 0
            RemovedSizeBytes = 0
        }
        
        # Calcular tamanhos se os arquivos ainda existirem
        foreach ($file in $BackedUpFiles) {
            if (Test-Path $file) {
                $reportData.BackupSizeBytes += (Get-Item $file).Length
            }
        }
        
        $fileName = "File-Cleanup-$ClienteId-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
        $filePath = Join-Path $OutputPath $fileName
        
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
        
        $reportData | ConvertTo-Json -Depth 3 | Out-File -FilePath $filePath -Encoding UTF8
        
        Write-Log "Relatório de limpeza de arquivos exportado: $filePath" -Level Info
        return $filePath
    }
    catch {
        Write-Log "Erro ao exportar relatório de arquivos: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Compress-ClienteFiles {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [array]$Files,
        [string]$OutputPath = ".\Archives"
    )
    
    try {
        if ($Files.Count -eq 0) {
            Write-Log "Nenhum arquivo para compactar" -Level Warning
            return $null
        }
        
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $archiveName = "Cliente_$ClienteId_$timestamp.zip"
        $archivePath = Join-Path $OutputPath $archiveName
        
        # Usar .NET para criar o arquivo ZIP
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        
        $archive = [System.IO.Compression.ZipFile]::Open($archivePath, 'Create')
        
        foreach ($file in $Files) {
            if (Test-Path $file.FullName) {
                $entryName = $file.Name
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $file.FullName, $entryName)
            }
        }
        
        $archive.Dispose()
        
        Write-Log "Arquivo compactado criado: $archivePath" -Level Info
        return $archivePath
    }
    catch {
        Write-Log "Erro ao compactar arquivos: $($_.Exception.Message)" -Level Error
        throw
    }
}

Export-ModuleMember -Function *