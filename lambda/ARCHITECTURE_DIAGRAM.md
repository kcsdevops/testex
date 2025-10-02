# 🏗️ TESTEX - Diagrama de Arquitetura AWS Lambda

```mermaid
graph LR
    subgraph "👥 Usuários"
        U1[👤 Cliente]
        U2[👨‍💼 Admin]
        U3[🖥️ Sistema Externo]
    end
    
    subgraph "🌐 Camada de API"
        AG[🌐 API Gateway]
        AL[⚡ API Lambda<br/>Roteamento]
    end
    
    subgraph "⚡ Funções Lambda"
        CP[📋 Contract Processor<br/>Lógica de Negócio]
        DM[🗄️ Database Manager<br/>Operações CRUD]
        FH[📁 File Handler<br/>Gestão de Arquivos]
        NS[📧 Notification Service<br/>Sistema de Email]
    end
    
    subgraph "🗄️ Armazenamento"
        DB[(DynamoDB<br/>📊 Contratos<br/>👥 Clientes<br/>📝 Logs)]
        S3F[(S3 Files<br/>📄 Documentos)]
        S3A[(S3 Archives<br/>📦 Arquivos)]
        S3B[(S3 Backups<br/>💾 Backups)]
    end
    
    subgraph "📧 Comunicação"
        SES[Amazon SES<br/>📤 Email]
        CW[CloudWatch<br/>📊 Logs/Métricas]
    end
    
    %% Fluxo principal
    U1 --> AG
    U2 --> AG
    U3 --> AG
    
    AG --> AL
    AL --> CP
    AL --> DM
    AL --> FH
    AL --> NS
    
    %% Interações entre Lambda functions
    CP --> DM
    CP --> FH
    CP --> NS
    
    FH --> DM
    NS --> DM
    
    %% Conexões com armazenamento
    DM <--> DB
    FH <--> S3F
    FH <--> S3A
    FH <--> S3B
    
    %% Notificações
    NS --> SES
    
    %% Monitoramento
    AL --> CW
    CP --> CW
    DM --> CW
    FH --> CW
    NS --> CW
    
    %% Styling
    classDef users fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef api fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef lambda fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef storage fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    classDef services fill:#FF5722,stroke:#BF360C,stroke-width:2px,color:#fff
    
    class U1,U2,U3 users
    class AG,AL api
    class CP,DM,FH,NS lambda
    class DB,S3F,S3A,S3B storage
    class SES,CW services
```

## 📋 Componentes do Sistema

### 👥 **Camada de Usuários**
- **Cliente**: Usuários finais do sistema
- **Administrador**: Gestores do sistema
- **Sistema Externo**: Integrações de terceiros

### 🌐 **Camada de API** 
- **API Gateway**: Ponto de entrada único para todas as requisições
- **API Lambda**: Função de roteamento e validação de requisições

### ⚡ **Funções Lambda Core**
- **Contract Processor**: Lógica principal de negócio para contratos
- **Database Manager**: Todas as operações de banco de dados
- **File Handler**: Gestão de arquivos e documentos
- **Notification Service**: Sistema de notificações por email

### 🗄️ **Camada de Dados**
- **DynamoDB**: Base de dados NoSQL para contratos, clientes e logs
- **S3 Buckets**: Armazenamento de arquivos, backups e templates

### 📧 **Serviços de Comunicação**
- **Amazon SES**: Serviço de envio de emails
- **CloudWatch**: Monitoramento e logs do sistema

---

# 🔄 Fluxo de Terminação de Contrato

```mermaid
sequenceDiagram
    participant C as 👤 Cliente
    participant AG as 🌐 API Gateway
    participant AL as ⚡ API Lambda
    participant CP as 📋 Contract Processor
    participant DM as 🗄️ Database Manager
    participant FH as 📁 File Handler
    participant NS as 📧 Notification Service
    participant DB as 💾 DynamoDB
    participant S3 as 📦 S3
    participant SES as 📧 Amazon SES
    
    C->>AG: POST /api/contracts/{id}/terminate
    AG->>AL: Encaminhar requisição
    AL->>AL: Validar autenticação
    AL->>CP: Processar terminação
    
    CP->>DM: Validar contrato
    DM->>DB: Buscar dados do contrato
    DB-->>DM: Dados do contrato
    DM-->>CP: Contrato válido
    
    CP->>FH: Fazer backup dos dados
    FH->>S3: Salvar backup
    S3-->>FH: Backup salvo
    FH-->>CP: Backup confirmado
    
    CP->>DM: Atualizar status do contrato
    DM->>DB: UPDATE status = 'TERMINATED'
    DB-->>DM: Atualização confirmada
    DM-->>CP: Status atualizado
    
    CP->>DM: Criar log de auditoria
    DM->>DB: INSERT audit log
    DB-->>DM: Log criado
    DM-->>CP: Auditoria registrada
    
    CP->>NS: Enviar notificação
    NS->>S3: Carregar template de email
    S3-->>NS: Template carregado
    NS->>SES: Enviar email
    SES-->>NS: Email enviado
    NS-->>CP: Notificação enviada
    
    CP->>FH: Arquivar documentos
    FH->>S3: Mover para archives
    S3-->>FH: Arquivos movidos
    FH-->>CP: Arquivamento concluído
    
    CP-->>AL: Processo concluído
    AL-->>AG: Resposta de sucesso
    AG-->>C: 200 OK + dados do contrato terminado
```

## 🎯 **Principais Benefícios da Arquitetura**

### ✅ **Escalabilidade**
- Auto-scaling das funções Lambda
- DynamoDB com capacidade sob demanda
- S3 com armazenamento ilimitado

### ✅ **Confiabilidade**
- Retry automático em caso de falhas
- Backup automático de dados críticos
- Logs detalhados para auditoria

### ✅ **Segurança**
- IAM roles com privilégios mínimos
- Criptografia em trânsito e em repouso
- Logs de auditoria completos

### ✅ **Custo-Efetivo**
- Pay-per-use em todas as camadas
- Sem infraestrutura para gerenciar
- Otimização automática de recursos

### ✅ **Manutenibilidade**
- Separação clara de responsabilidades
- Código modular e testável
- Monitoramento integrado