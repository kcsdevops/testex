# Módulo de Operações UMA
# Funções para integração com o sistema UMA

function Connect-ToUMA {
    param(
        [Parameter(Mandatory)]
        [string]$ApiUrl,
        [Parameter(Mandatory)]
        [string]$ApiKey,
        [int]$TimeoutSeconds = 60
    )
    
    try {
        $script:UMAConfig = @{
            ApiUrl = $ApiUrl.TrimEnd('/')
            ApiKey = $ApiKey
            Timeout = $TimeoutSeconds
            Headers = @{
                'Authorization' = "Bearer $ApiKey"
                'Content-Type' = 'application/json'
                'User-Agent' = 'TESTEX-Automation/1.0'
            }
        }
        
        # Testar conectividade
        $testEndpoint = "$($script:UMAConfig.ApiUrl)/health"
        $response = Invoke-RestMethod -Uri $testEndpoint -Headers $script:UMAConfig.Headers -TimeoutSec $TimeoutSeconds -Method Get
        
        Write-Log "Conectado ao sistema UMA: $ApiUrl" -Level Info
        return $true
    }
    catch {
        Write-Log "Erro ao conectar ao UMA: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Get-UMAClientInfo {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId
    )
    
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/clients/$ClienteId"
        
        $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -TimeoutSec $script:UMAConfig.Timeout -Method Get
        
        Write-Log "Informações do cliente $ClienteId obtidas do UMA" -Level Info
        
        return [PSCustomObject]@{
            ClienteId = $response.clientId
            Nome = $response.name
            Status = $response.status
            DataCriacao = [DateTime]::Parse($response.createdDate)
            Configuracoes = $response.settings
            Servicos = $response.services
        }
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Log "Cliente $ClienteId não encontrado no UMA" -Level Warning
            return $null
        }
        else {
            Write-Log "Erro ao consultar cliente no UMA: $($_.Exception.Message)" -Level Error
            throw
        }
    }
}

function Disable-UMAClient {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [string]$Motivo = "Terminação de contrato",
        [switch]$WhatIf
    )
    
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/clients/$ClienteId/disable"
        
        $body = @{
            reason = $Motivo
            disabledBy = $env:USERNAME
            disabledDate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        } | ConvertTo-Json
        
        if ($WhatIf) {
            Write-Log "SIMULAÇÃO: Desabilitaria cliente $ClienteId no UMA" -Level Info
            return $true
        }
        
        $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -Body $body -TimeoutSec $script:UMAConfig.Timeout -Method Post
        
        Write-Log "Cliente $ClienteId desabilitado no UMA" -Level Info
        return $true
    }
    catch {
        Write-Log "Erro ao desabilitar cliente no UMA: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Remove-UMAClientServices {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [array]$Services = @(),
        [switch]$WhatIf
    )
    
    try {
        if ($Services.Count -eq 0) {
            # Obter todos os serviços do cliente
            $clientInfo = Get-UMAClientInfo -ClienteId $ClienteId
            if ($clientInfo) {
                $Services = $clientInfo.Servicos
            }
        }
        
        $removedServices = @()
        
        foreach ($service in $Services) {
            $endpoint = "$($script:UMAConfig.ApiUrl)/clients/$ClienteId/services/$service"
            
            if ($WhatIf) {
                Write-Log "SIMULAÇÃO: Removeria serviço $service do cliente $ClienteId" -Level Info
            }
            else {
                $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -TimeoutSec $script:UMAConfig.Timeout -Method Delete
                Write-Log "Serviço $service removido do cliente $ClienteId" -Level Info
            }
            
            $removedServices += $service
        }
        
        return $removedServices
    }
    catch {
        Write-Log "Erro ao remover serviços do UMA: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Update-UMAClientStatus {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [Parameter(Mandatory)]
        [ValidateSet("ACTIVE", "INACTIVE", "TERMINATED", "SUSPENDED")]
        [string]$NovoStatus,
        [string]$Observacoes = ""
    )
    
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/clients/$ClienteId/status"
        
        $body = @{
            status = $NovoStatus
            notes = $Observacoes
            updatedBy = $env:USERNAME
            updatedDate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -Body $body -TimeoutSec $script:UMAConfig.Timeout -Method Put
        
        Write-Log "Status do cliente $ClienteId atualizado para $NovoStatus no UMA" -Level Info
        return $true
    }
    catch {
        Write-Log "Erro ao atualizar status no UMA: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Get-UMAClientLogs {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [DateTime]$StartDate = (Get-Date).AddDays(-30),
        [DateTime]$EndDate = (Get-Date),
        [int]$Limit = 100
    )
    
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/clients/$ClienteId/logs"
        
        $queryParams = @{
            startDate = $StartDate.ToString("yyyy-MM-ddTHH:mm:ssZ")
            endDate = $EndDate.ToString("yyyy-MM-ddTHH:mm:ssZ")
            limit = $Limit
        }
        
        $queryString = ($queryParams.GetEnumerator() | ForEach-Object { "$($_.Key)=$([System.Web.HttpUtility]::UrlEncode($_.Value))" }) -join "&"
        $fullEndpoint = "$endpoint?$queryString"
        
        $response = Invoke-RestMethod -Uri $fullEndpoint -Headers $script:UMAConfig.Headers -TimeoutSec $script:UMAConfig.Timeout -Method Get
        
        Write-Log "Obtidos $($response.logs.Count) logs do cliente $ClienteId do UMA" -Level Info
        
        $logs = @()
        foreach ($log in $response.logs) {
            $logs += [PSCustomObject]@{
                Timestamp = [DateTime]::Parse($log.timestamp)
                Level = $log.level
                Message = $log.message
                Component = $log.component
                UserId = $log.userId
            }
        }
        
        return $logs
    }
    catch {
        Write-Log "Erro ao obter logs do UMA: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Invoke-UMAClientPurge {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [switch]$WhatIf,
        [switch]$Force
    )
    
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/clients/$ClienteId/purge"
        
        $body = @{
            force = $Force.IsPresent
            requestedBy = $env:USERNAME
            requestedDate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        } | ConvertTo-Json
        
        if ($WhatIf) {
            Write-Log "SIMULAÇÃO: Executaria purge do cliente $ClienteId no UMA" -Level Info
            return @{
                Success = $true
                PurgeId = "SIMULATED-$(Get-Random)"
                Status = "SIMULATED"
            }
        }
        
        $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -Body $body -TimeoutSec $script:UMAConfig.Timeout -Method Post
        
        Write-Log "Purge iniciado para cliente $ClienteId no UMA (ID: $($response.purgeId))" -Level Info
        
        return @{
            Success = $true
            PurgeId = $response.purgeId
            Status = $response.status
        }
    }
    catch {
        Write-Log "Erro ao executar purge no UMA: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Get-UMAPurgeStatus {
    param(
        [Parameter(Mandatory)]
        [string]$PurgeId
    )
    
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/purge/$PurgeId/status"
        
        $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -TimeoutSec $script:UMAConfig.Timeout -Method Get
        
        return [PSCustomObject]@{
            PurgeId = $response.purgeId
            Status = $response.status
            Progress = $response.progress
            StartTime = [DateTime]::Parse($response.startTime)
            EndTime = if ($response.endTime) { [DateTime]::Parse($response.endTime) } else { $null }
            ErrorMessage = $response.errorMessage
            Details = $response.details
        }
    }
    catch {
        Write-Log "Erro ao consultar status do purge: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Test-UMAConnectivity {
    try {
        $endpoint = "$($script:UMAConfig.ApiUrl)/health"
        $response = Invoke-RestMethod -Uri $endpoint -Headers $script:UMAConfig.Headers -TimeoutSec 10 -Method Get
        
        if ($response.status -eq "healthy") {
            Write-Log "Conectividade com UMA confirmada" -Level Info
            return $true
        }
        else {
            Write-Log "UMA reportou status não saudável: $($response.status)" -Level Warning
            return $false
        }
    }
    catch {
        Write-Log "Falha na conectividade com UMA: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Export-UMACleanupReport {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [string]$PurgeId,
        [array]$RemovedServices,
        [string]$OutputPath = ".\Reports"
    )
    
    try {
        $reportData = @{
            ClienteId = $ClienteId
            DateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            PurgeId = $PurgeId
            RemovedServices = $RemovedServices
            TotalServices = $RemovedServices.Count
            UMAEndpoint = $script:UMAConfig.ApiUrl
        }
        
        $fileName = "UMA-Cleanup-$ClienteId-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
        $filePath = Join-Path $OutputPath $fileName
        
        if (-not (Test-Path $OutputPath)) {
            New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
        }
        
        $reportData | ConvertTo-Json -Depth 3 | Out-File -FilePath $filePath -Encoding UTF8
        
        Write-Log "Relatório de limpeza do UMA exportado: $filePath" -Level Info
        return $filePath
    }
    catch {
        Write-Log "Erro ao exportar relatório do UMA: $($_.Exception.Message)" -Level Error
        throw
    }
}

Export-ModuleMember -Function *