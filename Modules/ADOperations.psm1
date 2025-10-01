# Módulo de Operações do Active Directory
# Funções para gerenciar usuários e grupos no AD

Import-Module ActiveDirectory -ErrorAction SilentlyContinue

function Connect-ToActiveDirectory {
    param(
        [string]$Server = $null,
        [PSCredential]$Credential = $null
    )
    
    try {
        if ($Server -and $Credential) {
            $script:ADConnection = @{
                Server = $Server
                Credential = $Credential
            }
        }
        
        Write-Log "Conectado ao Active Directory: $Server" -Level Info
        return $true
    }
    catch {
        Write-Log "Erro ao conectar ao AD: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Get-ADUsersByClient {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId
    )
    
    try {
        $searchBase = "OU=Users,DC=empresa,DC=local"
        $filter = "Description -like '*$ClienteId*'"
        
        $users = Get-ADUser -Filter $filter -SearchBase $searchBase -Properties Description, EmployeeID
        
        Write-Log "Encontrados $($users.Count) usuários para o cliente $ClienteId" -Level Info
        return $users
    }
    catch {
        Write-Log "Erro ao buscar usuários do AD: $($_.Exception.Message)" -Level Error
        return @()
    }
}

function Remove-ADUsersByClient {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [switch]$WhatIf
    )
    
    try {
        $users = Get-ADUsersByClient -ClienteId $ClienteId
        $removedUsers = @()
        
        foreach ($user in $users) {
            if ($WhatIf) {
                Write-Log "SIMULAÇÃO: Removeria usuário $($user.SamAccountName)" -Level Info
            }
            else {
                # Desabilitar primeiro
                Disable-ADAccount -Identity $user.SamAccountName
                Write-Log "Usuário $($user.SamAccountName) desabilitado" -Level Info
                
                # Mover para OU de exclusão
                $excludeOU = "OU=ToDelete,DC=empresa,DC=local"
                Move-ADObject -Identity $user.DistinguishedName -TargetPath $excludeOU
                Write-Log "Usuário $($user.SamAccountName) movido para OU de exclusão" -Level Info
                
                $removedUsers += $user.SamAccountName
            }
        }
        
        return $removedUsers
    }
    catch {
        Write-Log "Erro ao remover usuários do AD: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Get-ADGroupsByClient {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId
    )
    
    try {
        $searchBase = "OU=Groups,DC=empresa,DC=local"
        $filter = "Description -like '*$ClienteId*' -or Name -like '*$ClienteId*'"
        
        $groups = Get-ADGroup -Filter $filter -SearchBase $searchBase -Properties Description
        
        Write-Log "Encontrados $($groups.Count) grupos para o cliente $ClienteId" -Level Info
        return $groups
    }
    catch {
        Write-Log "Erro ao buscar grupos do AD: $($_.Exception.Message)" -Level Error
        return @()
    }
}

function Remove-ADGroupsByClient {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [switch]$WhatIf
    )
    
    try {
        $groups = Get-ADGroupsByClient -ClienteId $ClienteId
        $removedGroups = @()
        
        foreach ($group in $groups) {
            if ($WhatIf) {
                Write-Log "SIMULAÇÃO: Removeria grupo $($group.Name)" -Level Info
            }
            else {
                # Remover todos os membros primeiro
                $members = Get-ADGroupMember -Identity $group.Name
                foreach ($member in $members) {
                    Remove-ADGroupMember -Identity $group.Name -Members $member -Confirm:$false
                }
                
                # Remover o grupo
                Remove-ADGroup -Identity $group.Name -Confirm:$false
                Write-Log "Grupo $($group.Name) removido" -Level Info
                
                $removedGroups += $group.Name
            }
        }
        
        return $removedGroups
    }
    catch {
        Write-Log "Erro ao remover grupos do AD: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Test-ADConnectivity {
    try {
        $domain = Get-ADDomain
        Write-Log "Conectividade com AD confirmada: $($domain.DNSRoot)" -Level Info
        return $true
    }
    catch {
        Write-Log "Falha na conectividade com AD: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Export-ADCleanupReport {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [array]$RemovedUsers,
        [array]$RemovedGroups,
        [string]$OutputPath = ".\Reports"
    )
    
    try {
        $reportData = @{
            ClienteId = $ClienteId
            DateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            RemovedUsers = $RemovedUsers
            RemovedGroups = $RemovedGroups
            TotalUsers = $RemovedUsers.Count
            TotalGroups = $RemovedGroups.Count
        }
        
        $fileName = "AD-Cleanup-$ClienteId-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
        $filePath = Join-Path $OutputPath $fileName
        
        $reportData | ConvertTo-Json -Depth 3 | Out-File -FilePath $filePath -Encoding UTF8
        
        Write-Log "Relatório de limpeza do AD exportado: $filePath" -Level Info
        return $filePath
    }
    catch {
        Write-Log "Erro ao exportar relatório do AD: $($_.Exception.Message)" -Level Error
        throw
    }
}

Export-ModuleMember -Function *