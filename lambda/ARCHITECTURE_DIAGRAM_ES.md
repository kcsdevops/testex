# 🏗️ TESTEX - Diagrama de Arquitectura AWS Lambda (Español)

```mermaid
graph LR
    subgraph "👥 Usuarios"
        U1[👤 Cliente]
        U2[👨‍💼 Administrador]
        U3[🖥️ Sistema Externo]
    end
    
    subgraph "🌐 Capa de API"
        AG[🌐 API Gateway]
        AL[⚡ API Lambda<br/>Enrutamiento]
    end
    
    subgraph "⚡ Funciones Lambda"
        CP[📋 Procesador de Contratos<br/>Lógica de Negocio]
        DM[🗄️ Gestor de BD<br/>Operaciones CRUD]
        FH[📁 Manejador de Archivos<br/>Gestión de Archivos]
        NS[📧 Servicio de Notificación<br/>Sistema de Email]
    end
    
    subgraph "🗄️ Almacenamiento"
        DB[(DynamoDB<br/>📊 Contratos<br/>👥 Clientes<br/>📝 Logs)]
        S3F[(S3 Archivos<br/>📄 Documentos)]
        S3A[(S3 Archivos<br/>📦 Archivos)]
        S3B[(S3 Backups<br/>💾 Respaldos)]
    end
    
    subgraph "📧 Comunicación"
        SES[Amazon SES<br/>📤 Email]
        CW[CloudWatch<br/>📊 Logs/Métricas]
    end
    
    %% Flujo principal
    U1 --> AG
    U2 --> AG
    U3 --> AG
    
    AG --> AL
    AL --> CP
    AL --> DM
    AL --> FH
    AL --> NS
    
    %% Interacciones entre funciones Lambda
    CP --> DM
    CP --> FH
    CP --> NS
    
    FH --> DM
    NS --> DM
    
    %% Conexiones con almacenamiento
    DM <--> DB
    FH <--> S3F
    FH <--> S3A
    FH <--> S3B
    
    %% Notificaciones
    NS --> SES
    
    %% Monitoreo
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

## 📋 Componentes del Sistema

### 👥 **Capa de Usuarios**

- **Cliente**: Usuarios finales del sistema
- **Administrador**: Gestores del sistema
- **Sistema Externo**: Integraciones de terceros

### 🌐 **Capa de API**

- **API Gateway**: Punto de entrada único para todas las peticiones
- **API Lambda**: Función de enrutamiento y validación de peticiones

### ⚡ **Funciones Lambda Core**

- **Procesador de Contratos**: Lógica principal de negocio para contratos
- **Gestor de BD**: Todas las operaciones de base de datos
- **Manejador de Archivos**: Gestión de archivos y documentos
- **Servicio de Notificación**: Sistema de notificaciones por email

### 🗄️ **Capa de Datos**

- **DynamoDB**: Base de datos NoSQL para contratos, clientes y logs
- **S3 Buckets**: Almacenamiento de archivos, respaldos y plantillas

### 📧 **Servicios de Comunicación**

- **Amazon SES**: Servicio de envío de emails
- **CloudWatch**: Monitoreo y logs del sistema

---

# 🔄 Flujo de Terminación de Contrato

```mermaid
sequenceDiagram
    participant C as 👤 Cliente
    participant AG as 🌐 API Gateway
    participant AL as ⚡ API Lambda
    participant CP as 📋 Procesador de Contratos
    participant DM as 🗄️ Gestor de BD
    participant FH as 📁 Manejador de Archivos
    participant NS as 📧 Servicio de Notificación
    participant DB as 💾 DynamoDB
    participant S3 as 📦 S3
    participant SES as 📧 Amazon SES
    
    C->>AG: POST /api/contracts/{id}/terminate
    AG->>AL: Reenviar petición
    AL->>AL: Validar autenticación
    AL->>CP: Procesar terminación
    
    CP->>DM: Validar contrato
    DM->>DB: Buscar datos del contrato
    DB-->>DM: Datos del contrato
    DM-->>CP: Contrato válido
    
    CP->>FH: Hacer respaldo de datos
    FH->>S3: Guardar respaldo
    S3-->>FH: Respaldo guardado
    FH-->>CP: Respaldo confirmado
    
    CP->>DM: Actualizar estado del contrato
    DM->>DB: UPDATE status = 'TERMINATED'
    DB-->>DM: Actualización confirmada
    DM-->>CP: Estado actualizado
    
    CP->>DM: Crear log de auditoría
    DM->>DB: INSERT audit log
    DB-->>DM: Log creado
    DM-->>CP: Auditoría registrada
    
    CP->>NS: Enviar notificación
    NS->>S3: Cargar plantilla de email
    S3-->>NS: Plantilla cargada
    NS->>SES: Enviar email
    SES-->>NS: Email enviado
    NS-->>CP: Notificación enviada
    
    CP->>FH: Archivar documentos
    FH->>S3: Mover a archivos
    S3-->>FH: Archivos movidos
    FH-->>CP: Archivado completado
    
    CP-->>AL: Proceso completado
    AL-->>AG: Respuesta de éxito
    AG-->>C: 200 OK + datos del contrato terminado
```

## 🎯 **Principales Beneficios de la Arquitectura**

### ✅ **Escalabilidad**

- Auto-escalado de las funciones Lambda
- DynamoDB con capacidad bajo demanda
- S3 con almacenamiento ilimitado

### ✅ **Confiabilidad**

- Reintento automático en caso de fallos
- Respaldo automático de datos críticos
- Logs detallados para auditoría

### ✅ **Seguridad**

- Roles IAM con privilegios mínimos
- Cifrado en tránsito y en reposo
- Logs de auditoría completos

### ✅ **Costo-Efectivo**

- Pago por uso en todas las capas
- Sin infraestructura que gestionar
- Optimización automática de recursos

### ✅ **Mantenibilidad**

- Separación clara de responsabilidades
- Código modular y testeable
- Monitoreo integrado