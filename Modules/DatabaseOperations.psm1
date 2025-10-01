# Módulo de Operações de Banco de Dados
# Funções para operações SQL Server

function Connect-ToDatabase {
    param(
        [Parameter(Mandatory)]
        [string]$ServerInstance,
        [string]$Database = "TerminacaoContratos",
        [PSCredential]$Credential = $null,
        [switch]$IntegratedSecurity
    )
    
    try {
        if ($IntegratedSecurity) {
            $connectionString = "Server=$ServerInstance;Database=$Database;Integrated Security=True;Connection Timeout=30;"
        }
        else {
            $username = $Credential.UserName
            $password = $Credential.GetNetworkCredential().Password
            $connectionString = "Server=$ServerInstance;Database=$Database;User Id=$username;Password=$password;Connection Timeout=30;"
        }
        
        $script:DatabaseConnection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
        $script:DatabaseConnection.Open()
        
        Write-Log "Conectado ao banco de dados: $ServerInstance/$Database" -Level Info
        return $true
    }
    catch {
        Write-Log "Erro ao conectar ao banco: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Get-ClienteInfo {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId
    )
    
    try {
        $query = @"
            SELECT 
                ClienteId,
                NomeCliente,
                Status,
                DataCriacao,
                DataTermino,
                ResponsavelTecnico,
                ObservacoesTermino
            FROM Clientes 
            WHERE ClienteId = @ClienteId
"@
        
        $command = New-Object System.Data.SqlClient.SqlCommand($query, $script:DatabaseConnection)
        $command.Parameters.AddWithValue("@ClienteId", $ClienteId)
        
        $adapter = New-Object System.Data.SqlClient.SqlDataAdapter($command)
        $dataTable = New-Object System.Data.DataTable
        $adapter.Fill($dataTable)
        
        if ($dataTable.Rows.Count -eq 0) {
            Write-Log "Cliente $ClienteId não encontrado" -Level Warning
            return $null
        }
        
        $cliente = $dataTable.Rows[0]
        Write-Log "Cliente encontrado: $($cliente.NomeCliente)" -Level Info
        
        return [PSCustomObject]@{
            ClienteId = $cliente.ClienteId
            NomeCliente = $cliente.NomeCliente
            Status = $cliente.Status
            DataCriacao = $cliente.DataCriacao
            DataTermino = $cliente.DataTermino
            ResponsavelTecnico = $cliente.ResponsavelTecnico
            ObservacoesTermino = $cliente.ObservacoesTermino
        }
    }
    catch {
        Write-Log "Erro ao consultar cliente: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Update-ClienteStatus {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [Parameter(Mandatory)]
        [string]$NovoStatus,
        [string]$Observacoes = ""
    )
    
    try {
        $query = @"
            UPDATE Clientes 
            SET 
                Status = @NovoStatus,
                DataTermino = GETDATE(),
                ObservacoesTermino = @Observacoes,
                DataUltimaAtualizacao = GETDATE()
            WHERE ClienteId = @ClienteId
"@
        
        $command = New-Object System.Data.SqlClient.SqlCommand($query, $script:DatabaseConnection)
        $command.Parameters.AddWithValue("@ClienteId", $ClienteId)
        $command.Parameters.AddWithValue("@NovoStatus", $NovoStatus)
        $command.Parameters.AddWithValue("@Observacoes", $Observacoes)
        
        $rowsAffected = $command.ExecuteNonQuery()
        
        if ($rowsAffected -gt 0) {
            Write-Log "Status do cliente $ClienteId atualizado para: $NovoStatus" -Level Info
            return $true
        }
        else {
            Write-Log "Nenhuma linha afetada ao atualizar cliente $ClienteId" -Level Warning
            return $false
        }
    }
    catch {
        Write-Log "Erro ao atualizar status do cliente: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Backup-Database {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [string]$BackupPath = ".\Backups"
    )
    
    try {
        if (-not (Test-Path $BackupPath)) {
            New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
        }
        
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFileName = "Backup_$ClienteId_$timestamp.bak"
        $fullBackupPath = Join-Path $BackupPath $backupFileName
        
        $query = @"
            BACKUP DATABASE TerminacaoContratos 
            TO DISK = @BackupPath
            WITH FORMAT, INIT, 
            NAME = 'Backup antes da terminacao do cliente $ClienteId',
            DESCRIPTION = 'Backup automatico antes da terminacao do contrato'
"@
        
        $command = New-Object System.Data.SqlClient.SqlCommand($query, $script:DatabaseConnection)
        $command.Parameters.AddWithValue("@BackupPath", $fullBackupPath)
        $command.CommandTimeout = 300  # 5 minutos
        
        Write-Log "Iniciando backup do banco de dados..." -Level Info
        $command.ExecuteNonQuery()
        
        Write-Log "Backup concluído: $fullBackupPath" -Level Info
        return $fullBackupPath
    }
    catch {
        Write-Log "Erro ao fazer backup: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Get-ClienteUsuarios {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId
    )
    
    try {
        $query = @"
            SELECT 
                UsuarioId,
                NomeUsuario,
                Email,
                Status,
                DataCriacao
            FROM Usuarios 
            WHERE ClienteId = @ClienteId
"@
        
        $command = New-Object System.Data.SqlClient.SqlCommand($query, $script:DatabaseConnection)
        $command.Parameters.AddWithValue("@ClienteId", $ClienteId)
        
        $adapter = New-Object System.Data.SqlClient.SqlDataAdapter($command)
        $dataTable = New-Object System.Data.DataTable
        $adapter.Fill($dataTable)
        
        $usuarios = @()
        foreach ($row in $dataTable.Rows) {
            $usuarios += [PSCustomObject]@{
                UsuarioId = $row.UsuarioId
                NomeUsuario = $row.NomeUsuario
                Email = $row.Email
                Status = $row.Status
                DataCriacao = $row.DataCriacao
            }
        }
        
        Write-Log "Encontrados $($usuarios.Count) usuários para o cliente $ClienteId" -Level Info
        return $usuarios
    }
    catch {
        Write-Log "Erro ao consultar usuários: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Remove-ClienteData {
    param(
        [Parameter(Mandatory)]
        [string]$ClienteId,
        [switch]$WhatIf
    )
    
    try {
        $tables = @("Usuarios", "ClienteConfiguracoes", "Logs", "Arquivos")
        $removedRecords = @{}
        
        foreach ($table in $tables) {
            if ($WhatIf) {
                $countQuery = "SELECT COUNT(*) FROM $table WHERE ClienteId = @ClienteId"
                $countCommand = New-Object System.Data.SqlClient.SqlCommand($countQuery, $script:DatabaseConnection)
                $countCommand.Parameters.AddWithValue("@ClienteId", $ClienteId)
                $count = $countCommand.ExecuteScalar()
                
                Write-Log "SIMULAÇÃO: Removeria $count registros da tabela $table" -Level Info
                $removedRecords[$table] = $count
            }
            else {
                $deleteQuery = "DELETE FROM $table WHERE ClienteId = @ClienteId"
                $deleteCommand = New-Object System.Data.SqlClient.SqlCommand($deleteQuery, $script:DatabaseConnection)
                $deleteCommand.Parameters.AddWithValue("@ClienteId", $ClienteId)
                $rowsAffected = $deleteCommand.ExecuteNonQuery()
                
                Write-Log "Removidos $rowsAffected registros da tabela $table" -Level Info
                $removedRecords[$table] = $rowsAffected
            }
        }
        
        return $removedRecords
    }
    catch {
        Write-Log "Erro ao remover dados do cliente: $($_.Exception.Message)" -Level Error
        throw
    }
}

function Test-DatabaseConnectivity {
    try {
        $query = "SELECT 1 as TestResult"
        $command = New-Object System.Data.SqlClient.SqlCommand($query, $script:DatabaseConnection)
        $result = $command.ExecuteScalar()
        
        if ($result -eq 1) {
            Write-Log "Conectividade com banco de dados confirmada" -Level Info
            return $true
        }
        else {
            Write-Log "Teste de conectividade falhou" -Level Error
            return $false
        }
    }
    catch {
        Write-Log "Falha na conectividade com banco: $($_.Exception.Message)" -Level Error
        return $false
    }
}

function Close-DatabaseConnection {
    try {
        if ($script:DatabaseConnection -and $script:DatabaseConnection.State -eq 'Open') {
            $script:DatabaseConnection.Close()
            $script:DatabaseConnection.Dispose()
            Write-Log "Conexão com banco de dados fechada" -Level Info
        }
    }
    catch {
        Write-Log "Erro ao fechar conexão: $($_.Exception.Message)" -Level Warning
    }
}

Export-ModuleMember -Function *