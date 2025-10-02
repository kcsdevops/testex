# TESTEX - Fluxograma de Terminação de Contratos

```mermaid
flowchart TD
    Start([🚀 Início: Solicitação de Terminação]) --> ValidateUser{🔐 Validar Usuário?}
    
    ValidateUser -->|❌ Inválido| Unauthorized[🚫 Não Autorizado<br/>Retornar Erro 401]
    ValidateUser -->|✅ Válido| ValidateContract{📋 Validar<br/>Dados do Contrato?}
    
    ValidateContract -->|❌ Inválido| ValidationError[⚠️ Erro de Validação<br/>Retornar Erro 400]
    ValidateContract -->|✅ Válido| CheckStatus{🔍 Status do Contrato<br/>é ATIVO?}
    
    CheckStatus -->|❌ Não| StatusError[⚠️ Contrato não pode<br/>ser terminado<br/>Status inválido]
    CheckStatus -->|✅ Sim| BackupData[💾 Backup dos Dados<br/>para S3 Backups]
    
    BackupData --> UpdateDB[🗄️ Atualizar Banco:<br/>Status → TERMINATED<br/>Data de Terminação<br/>Motivo da Terminação]
    
    UpdateDB --> CreateAudit[📝 Criar Log de Auditoria<br/>Ação: CONTRACT_TERMINATED<br/>Timestamp: Now()]
    
    CreateAudit --> PrepareNotification[📧 Preparar Notificação<br/>Carregar template de email<br/>Substituir variáveis]
    
    PrepareNotification --> SendEmail[📤 Enviar Email via SES<br/>Para: Cliente<br/>Assunto: Terminação de Contrato]
    
    SendEmail --> CheckEmailStatus{📧 Email enviado<br/>com sucesso?}
    
    CheckEmailStatus -->|❌ Falha| EmailError[⚠️ Erro no envio<br/>Log do erro<br/>Continuar processo]
    CheckEmailStatus -->|✅ Sucesso| LogEmail[📋 Log da notificação<br/>Status: SENT<br/>Message ID: SES ID]
    
    EmailError --> ArchiveFiles
    LogEmail --> ArchiveFiles[📦 Arquivar Arquivos<br/>Mover para S3 Archives<br/>Criar ZIP se necessário]
    
    ArchiveFiles --> UpdateFileStatus[📁 Atualizar Status<br/>dos Arquivos<br/>Status → ARCHIVED]
    
    UpdateFileStatus --> FinalAudit[📝 Log Final de Auditoria<br/>Ação: TERMINATION_COMPLETED<br/>Status: SUCCESS]
    
    FinalAudit --> Success([✅ Sucesso<br/>Retornar dados do<br/>contrato terminado])
    
    %% Error handling paths
    Unauthorized --> End([🔚 Fim])
    ValidationError --> End
    StatusError --> End
    
    %% Exception handling
    BackupData -->|❌ Erro| BackupError[⚠️ Erro no Backup<br/>Log do erro<br/>Rollback se necessário]
    UpdateDB -->|❌ Erro| DBError[⚠️ Erro no Banco<br/>Log do erro<br/>Rollback backup]
    CreateAudit -->|❌ Erro| AuditError[⚠️ Erro no Audit<br/>Log do erro<br/>Continuar processo]
    
    BackupError --> ErrorResponse[❌ Resposta de Erro<br/>Status 500<br/>Detalhes do erro]
    DBError --> ErrorResponse
    AuditError --> PrepareNotification
    
    ErrorResponse --> End
    Success --> End
    
    %% Styling
    classDef startEnd fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    classDef process fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef decision fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef error fill:#F44336,stroke:#C62828,stroke-width:2px,color:#fff
    classDef success fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    
    class Start,End startEnd
    class BackupData,UpdateDB,CreateAudit,PrepareNotification,SendEmail,LogEmail,ArchiveFiles,UpdateFileStatus,FinalAudit process
    class ValidateUser,ValidateContract,CheckStatus,CheckEmailStatus decision
    class Unauthorized,ValidationError,StatusError,EmailError,BackupError,DBError,AuditError,ErrorResponse error
    class Success success
```

## 🔄 Fluxo Detalhado por Etapas

### 1. 🔐 **Validação e Autorização**
- Verificar token de autenticação
- Validar permissões do usuário
- Verificar formato dos dados de entrada

### 2. 📋 **Validação do Contrato**
- Verificar se contract_id existe
- Validar formato do ID (CT + alfanumérico)
- Confirmar que o contrato pertence ao cliente

### 3. 🔍 **Verificação de Status**
- Confirmar que o contrato está ATIVO
- Verificar se não há impedimentos para terminação
- Validar data de término não expirada

### 4. 💾 **Backup de Segurança**
- Criar backup completo dos dados do contrato
- Salvar no S3 Backups com timestamp
- Incluir metadados e arquivos relacionados

### 5. 🗄️ **Atualização do Banco de Dados**
- Alterar status para TERMINATED
- Adicionar data e hora de terminação
- Registrar motivo da terminação
- Atualizar campo updated_at

### 6. 📝 **Log de Auditoria**
- Criar registro de auditoria detalhado
- Incluir dados do usuário que fez a ação
- Registrar timestamp preciso
- Salvar detalhes da operação

### 7. 📧 **Notificação por Email**
- Carregar template apropriado do S3
- Substituir variáveis dinâmicas
- Enviar via Amazon SES
- Tratar erros de envio

### 8. 📦 **Arquivamento de Arquivos**
- Mover arquivos do contrato para S3 Archives
- Criar arquivo ZIP se múltiplos arquivos
- Atualizar metadados dos arquivos
- Manter referências no banco

### 9. ✅ **Finalização**
- Log final de sucesso
- Retornar dados atualizados do contrato
- Limpar recursos temporários

## ⚠️ **Tratamento de Erros**

### **Estratégias de Recuperação**
- **Rollback automático** em caso de falha crítica
- **Retry logic** para operações temporariamente falhas
- **Dead letter queues** para reprocessamento
- **Alertas automáticos** para administradores

### **Logs e Monitoramento**
- Todos os erros são logados no CloudWatch
- Métricas customizadas para acompanhamento
- Alertas configurados para falhas críticas
- Dashboard de monitoramento em tempo real

## 🎯 **Resultados Esperados**

### **Em Caso de Sucesso**
```json
{
  "status": "success",
  "data": {
    "contract_id": "CT001ABC",
    "status": "TERMINATED",
    "termination_date": "2025-10-02T15:30:00Z",
    "termination_reason": "MUTUAL_AGREEMENT",
    "backup_location": "s3://backups/CT001ABC/20251002_153000",
    "notification_sent": true,
    "files_archived": 3
  },
  "message": "Contract terminated successfully"
}
```

### **Em Caso de Erro**
```json
{
  "status": "error",
  "error": "VALIDATION_ERROR",
  "message": "Contract ID format is invalid",
  "details": {
    "field": "contract_id",
    "provided": "INVALID_ID",
    "expected_format": "CT[A-Z0-9]{3,20}"
  },
  "timestamp": "2025-10-02T15:30:00Z"
}
```