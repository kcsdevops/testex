-- TESTEX Database Initialization Script
-- Cria estrutura de banco de dados para testes

USE master;
GO

-- Criar database TESTEX_DB se não existir
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'TESTEX_DB')
BEGIN
    CREATE DATABASE TESTEX_DB;
END
GO

USE TESTEX_DB;
GO

-- Tabela de clientes
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Clientes')
BEGIN
    CREATE TABLE Clientes (
        Id NVARCHAR(50) PRIMARY KEY,
        Nome NVARCHAR(255) NOT NULL,
        Email NVARCHAR(255),
        Telefone NVARCHAR(50),
        Status NVARCHAR(50) DEFAULT 'ACTIVE',
        DataCriacao DATETIME2 DEFAULT GETDATE(),
        DataAtualizacao DATETIME2 DEFAULT GETDATE(),
        Observacoes NVARCHAR(MAX)
    );
END
GO

-- Tabela de contratos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Contratos')
BEGIN
    CREATE TABLE Contratos (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        ClienteId NVARCHAR(50) NOT NULL,
        NumeroContrato NVARCHAR(100) UNIQUE NOT NULL,
        Valor DECIMAL(10,2),
        DataInicio DATE,
        DataFim DATE,
        Status NVARCHAR(50) DEFAULT 'ACTIVE',
        TipoServico NVARCHAR(100),
        FOREIGN KEY (ClienteId) REFERENCES Clientes(Id)
    );
END
GO

-- Tabela de logs de operações
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'OperationLogs')
BEGIN
    CREATE TABLE OperationLogs (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        ClienteId NVARCHAR(50),
        OperationType NVARCHAR(100) NOT NULL,
        OperationDetails NVARCHAR(MAX),
        Timestamp DATETIME2 DEFAULT GETDATE(),
        UserId NVARCHAR(100),
        Success BIT DEFAULT 1,
        ErrorMessage NVARCHAR(MAX)
    );
END
GO

-- Inserir dados de exemplo
IF NOT EXISTS (SELECT * FROM Clientes WHERE Id = 'CLI001')
BEGIN
    INSERT INTO Clientes (Id, Nome, Email, Telefone, Status) VALUES
    ('CLI001', 'Empresa ABC Ltda', 'contato@empresaabc.com', '11999887766', 'ACTIVE'),
    ('CLI002', 'XYZ Corporation', 'admin@xyzcorp.com', '11888776655', 'ACTIVE'),
    ('CLI003', 'TechStart Solutions', 'info@techstart.com', '11777665544', 'INACTIVE'),
    ('CLI004', 'Global Services Inc', 'support@globalservices.com', '11666554433', 'ACTIVE'),
    ('CLI005', 'Local Business SA', 'contact@localbiz.com', '11555443322', 'TERMINATED');
END
GO

-- Inserir contratos de exemplo
IF NOT EXISTS (SELECT * FROM Contratos WHERE NumeroContrato = 'CONT-2024-001')
BEGIN
    INSERT INTO Contratos (ClienteId, NumeroContrato, Valor, DataInicio, DataFim, Status, TipoServico) VALUES
    ('CLI001', 'CONT-2024-001', 15000.00, '2024-01-01', '2024-12-31', 'ACTIVE', 'Hosting'),
    ('CLI001', 'CONT-2024-002', 8500.00, '2024-06-01', '2025-05-31', 'ACTIVE', 'Support'),
    ('CLI002', 'CONT-2024-003', 25000.00, '2024-03-01', '2024-12-31', 'ACTIVE', 'Development'),
    ('CLI003', 'CONT-2023-001', 12000.00, '2023-01-01', '2023-12-31', 'EXPIRED', 'Consulting'),
    ('CLI004', 'CONT-2024-004', 30000.00, '2024-02-01', '2025-01-31', 'ACTIVE', 'Infrastructure'),
    ('CLI005', 'CONT-2023-002', 5000.00, '2023-06-01', '2023-12-31', 'TERMINATED', 'Maintenance');
END
GO

-- Stored Procedure para obter informações do cliente
CREATE OR ALTER PROCEDURE sp_GetClienteInfo
    @ClienteId NVARCHAR(50)
AS
BEGIN
    SELECT 
        c.*,
        COUNT(ct.Id) as TotalContratos,
        SUM(CASE WHEN ct.Status = 'ACTIVE' THEN 1 ELSE 0 END) as ContratosAtivos
    FROM Clientes c
    LEFT JOIN Contratos ct ON c.Id = ct.ClienteId
    WHERE c.Id = @ClienteId
    GROUP BY c.Id, c.Nome, c.Email, c.Telefone, c.Status, c.DataCriacao, c.DataAtualizacao, c.Observacoes;
END
GO

-- Stored Procedure para atualizar status do cliente
CREATE OR ALTER PROCEDURE sp_UpdateClienteStatus
    @ClienteId NVARCHAR(50),
    @NovoStatus NVARCHAR(50),
    @Observacoes NVARCHAR(MAX) = NULL
AS
BEGIN
    UPDATE Clientes 
    SET Status = @NovoStatus, 
        DataAtualizacao = GETDATE(),
        Observacoes = COALESCE(@Observacoes, Observacoes)
    WHERE Id = @ClienteId;
    
    -- Log da operação
    INSERT INTO OperationLogs (ClienteId, OperationType, OperationDetails, UserId)
    VALUES (@ClienteId, 'STATUS_UPDATE', 'Status alterado para ' + @NovoStatus, SYSTEM_USER);
END
GO

-- Stored Procedure para terminar contratos
CREATE OR ALTER PROCEDURE sp_TerminateClienteContratos
    @ClienteId NVARCHAR(50)
AS
BEGIN
    DECLARE @ContratosAfetados INT;
    
    UPDATE Contratos 
    SET Status = 'TERMINATED'
    WHERE ClienteId = @ClienteId AND Status != 'TERMINATED';
    
    SET @ContratosAfetados = @@ROWCOUNT;
    
    -- Log da operação
    INSERT INTO OperationLogs (ClienteId, OperationType, OperationDetails, UserId)
    VALUES (@ClienteId, 'CONTRACTS_TERMINATED', 
            'Terminados ' + CAST(@ContratosAfetados AS NVARCHAR(10)) + ' contratos', 
            SYSTEM_USER);
    
    SELECT @ContratosAfetados as ContratosTerminados;
END
GO

-- View para relatórios
CREATE OR ALTER VIEW vw_ClientesResumo AS
SELECT 
    c.Id,
    c.Nome,
    c.Email,
    c.Status,
    c.DataCriacao,
    COUNT(ct.Id) as TotalContratos,
    SUM(CASE WHEN ct.Status = 'ACTIVE' THEN 1 ELSE 0 END) as ContratosAtivos,
    SUM(CASE WHEN ct.Status = 'ACTIVE' THEN ct.Valor ELSE 0 END) as ValorAtivo
FROM Clientes c
LEFT JOIN Contratos ct ON c.Id = ct.ClienteId
GROUP BY c.Id, c.Nome, c.Email, c.Status, c.DataCriacao;
GO

PRINT 'TESTEX Database initialized successfully!';
PRINT 'Sample data loaded:';
SELECT 'Clientes' as Tabela, COUNT(*) as Registros FROM Clientes
UNION ALL
SELECT 'Contratos', COUNT(*) FROM Contratos;
GO