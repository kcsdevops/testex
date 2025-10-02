# 🔄 TESTEX - Diagrama de Flujo del Sistema (Español)

Sistema completo de terminación de contratos automatizado usando AWS Lambda.

## 🏗️ Arquitectura General del Sistema

```mermaid
flowchart TD
    %% Entrada
    START([🚀 Inicio de Solicitud]) --> AUTH{🔐 ¿Autenticación Válida?}
    
    %% Autenticación
    AUTH -->|❌ No| ERROR_AUTH[❌ Error de Autenticación]
    AUTH -->|✅ Sí| VALIDATE{📋 Validar Parámetros}
    
    %% Validación
    VALIDATE -->|❌ Inválido| ERROR_PARAM[❌ Parámetros Inválidos]
    VALIDATE -->|✅ Válido| ROUTE{🌐 Enrutar Solicitud}
    
    %% Enrutamiento
    ROUTE -->|📋 Contratos| CONTRACT_FLOW[Flujo de Contratos]
    ROUTE -->|📁 Archivos| FILE_FLOW[Flujo de Archivos]
    ROUTE -->|📧 Notificaciones| NOTIFY_FLOW[Flujo de Notificaciones]
    ROUTE -->|🗄️ Datos| DATA_FLOW[Flujo de Datos]
    
    %% Flujos específicos
    CONTRACT_FLOW --> CONTRACT_PROCESS[📋 Procesar Contrato]
    FILE_FLOW --> FILE_PROCESS[📁 Procesar Archivo]
    NOTIFY_FLOW --> NOTIFY_PROCESS[📧 Procesar Notificación]
    DATA_FLOW --> DATA_PROCESS[🗄️ Procesar Datos]
    
    %% Procesamiento
    CONTRACT_PROCESS --> DB_CHECK{🗄️ Verificar en BD}
    FILE_PROCESS --> S3_UPLOAD[📦 Subir a S3]
    NOTIFY_PROCESS --> SES_SEND[📤 Enviar vía SES]
    DATA_PROCESS --> DB_OPERATION[🗄️ Operación en BD]
    
    %% Verificación de datos
    DB_CHECK -->|❌ No Encontrado| ERROR_NOT_FOUND[❌ Contrato No Encontrado]
    DB_CHECK -->|✅ Encontrado| BACKUP[💾 Crear Respaldo]
    
    %% Respaldo y actualización
    BACKUP --> UPDATE_STATUS[🔄 Actualizar Estado]
    UPDATE_STATUS --> AUDIT_LOG[📝 Log de Auditoría]
    AUDIT_LOG --> SEND_NOTIFICATION[📧 Enviar Notificación]
    
    %% Finalización
    S3_UPLOAD --> SUCCESS
    SES_SEND --> SUCCESS
    DB_OPERATION --> SUCCESS
    SEND_NOTIFICATION --> SUCCESS[✅ Éxito]
    
    %% Errores
    ERROR_AUTH --> END_ERROR([❌ Fin con Error])
    ERROR_PARAM --> END_ERROR
    ERROR_NOT_FOUND --> END_ERROR
    
    %% Éxito
    SUCCESS --> RESPONSE[📋 Respuesta JSON]
    RESPONSE --> END_SUCCESS([✅ Fin con Éxito])
    
    %% Colores
    classDef startEnd fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef process fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef decision fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef error fill:#F44336,stroke:#C62828,stroke-width:2px,color:#fff
    classDef success fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    
    class START,END_SUCCESS,END_ERROR startEnd
    class CONTRACT_PROCESS,FILE_PROCESS,NOTIFY_PROCESS,DATA_PROCESS,BACKUP,UPDATE_STATUS,AUDIT_LOG,SEND_NOTIFICATION,S3_UPLOAD,SES_SEND,DB_OPERATION,RESPONSE process
    class AUTH,VALIDATE,ROUTE,DB_CHECK decision
    class ERROR_AUTH,ERROR_PARAM,ERROR_NOT_FOUND error
    class SUCCESS success
```

## 📋 Detalle de los Componentes

### 🔐 **Capa de Autenticación**

- Validación de tokens JWT
- Verificación de permisos
- Limitación de tasa

### 📋 **Procesamiento de Contratos**

- Validación de datos del contrato
- Verificación de estado actual
- Aplicación de reglas de negocio

### 💾 **Gestión de Datos**

- Operaciones CRUD en DynamoDB
- Respaldo automático de datos críticos
- Log de auditoría completo

### 📁 **Gestión de Archivos**

- Subida segura a S3
- Validación de tipos de archivo
- Control de versionado

### 📧 **Sistema de Notificaciones**

- Plantillas de email personalizables
- Envío vía Amazon SES
- Seguimiento de entrega

---

# 🔄 Flujo Específico de Terminación de Contrato

```mermaid
flowchart TD
    %% Inicio específico
    START_TERM([📋 Iniciar Terminación]) --> GET_CONTRACT[🔍 Buscar Contrato]
    
    %% Verificaciones iniciales
    GET_CONTRACT --> CONTRACT_EXISTS{📋 ¿Contrato Existe?}
    CONTRACT_EXISTS -->|❌ No| ERROR_404[❌ Contrato No Encontrado]
    CONTRACT_EXISTS -->|✅ Sí| CHECK_STATUS{📊 ¿Estado Permite Terminación?}
    
    %% Validación de estado
    CHECK_STATUS -->|❌ No| ERROR_STATUS[❌ Estado Inválido para Terminación]
    CHECK_STATUS -->|✅ Sí| CHECK_PERMISSION{🔐 ¿Cliente Tiene Permiso?}
    
    %% Validación de permiso
    CHECK_PERMISSION -->|❌ No| ERROR_PERMISSION[❌ Sin Permiso]
    CHECK_PERMISSION -->|✅ Sí| CREATE_BACKUP[💾 Crear Respaldo de Datos]
    
    %% Respaldo
    CREATE_BACKUP --> BACKUP_SUCCESS{💾 ¿Respaldo OK?}
    BACKUP_SUCCESS -->|❌ No| ERROR_BACKUP[❌ Falla en Respaldo]
    BACKUP_SUCCESS -->|✅ Sí| UPDATE_CONTRACT[🔄 Actualizar Estado del Contrato]
    
    %% Actualización
    UPDATE_CONTRACT --> UPDATE_SUCCESS{🔄 ¿Actualización OK?}
    UPDATE_SUCCESS -->|❌ No| ROLLBACK[🔄 Revertir Cambios]
    UPDATE_SUCCESS -->|✅ Sí| CREATE_AUDIT[📝 Crear Log de Auditoría]
    
    %% Auditoría
    CREATE_AUDIT --> AUDIT_SUCCESS{📝 ¿Log OK?}
    AUDIT_SUCCESS -->|❌ No| ERROR_AUDIT[❌ Falla en Log]
    AUDIT_SUCCESS -->|✅ Sí| NOTIFY_CLIENT[📧 Notificar Cliente]
    
    %% Notificación
    NOTIFY_CLIENT --> EMAIL_SUCCESS{📧 ¿Email OK?}
    EMAIL_SUCCESS -->|❌ No| LOG_EMAIL_ERROR[⚠️ Log Falla Email]
    EMAIL_SUCCESS -->|✅ Sí| ARCHIVE_DOCS[📦 Archivar Documentos]
    
    %% Archivado
    ARCHIVE_DOCS --> ARCHIVE_SUCCESS{📦 ¿Archivo OK?}
    ARCHIVE_SUCCESS -->|❌ No| LOG_ARCHIVE_ERROR[⚠️ Log Falla Archivo]
    ARCHIVE_SUCCESS -->|✅ Sí| FINALIZE[✅ Finalizar Proceso]
    
    %% Finalización
    LOG_EMAIL_ERROR --> FINALIZE
    LOG_ARCHIVE_ERROR --> FINALIZE
    FINALIZE --> RETURN_SUCCESS[📋 Retornar Datos del Contrato Terminado]
    
    %% Rollback
    ROLLBACK --> ERROR_ROLLBACK[❌ Error en Reversión]
    
    %% Fin
    RETURN_SUCCESS --> END_SUCCESS_TERM([✅ Terminación Completada])
    ERROR_404 --> END_ERROR_TERM([❌ Terminación Falló])
    ERROR_STATUS --> END_ERROR_TERM
    ERROR_PERMISSION --> END_ERROR_TERM
    ERROR_BACKUP --> END_ERROR_TERM
    ERROR_AUDIT --> END_ERROR_TERM
    ERROR_ROLLBACK --> END_ERROR_TERM
    
    %% Colores
    classDef startEnd fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef process fill:#2196F3,stroke:#1565C0,stroke-width:2px,color:#fff
    classDef decision fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#fff
    classDef error fill:#F44336,stroke:#C62828,stroke-width:2px,color:#fff
    classDef warning fill:#FF5722,stroke:#BF360C,stroke-width:2px,color:#fff
    classDef success fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    
    class START_TERM,END_SUCCESS_TERM,END_ERROR_TERM startEnd
    class GET_CONTRACT,CREATE_BACKUP,UPDATE_CONTRACT,CREATE_AUDIT,NOTIFY_CLIENT,ARCHIVE_DOCS,FINALIZE,RETURN_SUCCESS,ROLLBACK process
    class CONTRACT_EXISTS,CHECK_STATUS,CHECK_PERMISSION,BACKUP_SUCCESS,UPDATE_SUCCESS,AUDIT_SUCCESS,EMAIL_SUCCESS,ARCHIVE_SUCCESS decision
    class ERROR_404,ERROR_STATUS,ERROR_PERMISSION,ERROR_BACKUP,ERROR_AUDIT,ERROR_ROLLBACK error
    class LOG_EMAIL_ERROR,LOG_ARCHIVE_ERROR warning
```

## 📊 **Métricas y Monitoreo**

### 📈 **KPIs Principales**

- Tasa de éxito de terminaciones
- Tiempo promedio de procesamiento
- Número de rollbacks necesarios
- Tasa de entrega de emails

### 🚨 **Alertas Configuradas**

- Fallos consecutivos > 3
- Tiempo de respuesta > 30s
- Uso de memoria > 80%
- Errores de permiso > 10/min

### 📝 **Logs Detallados**

- Timestamp de cada operación
- ID de transacción única
- Datos de entrada/salida
- Stack trace de errores

---

## 🔒 **Seguridad y Cumplimiento**

### 🛡️ **Controles de Seguridad**

- Autenticación obligatoria
- Autorización basada en roles
- Cifrado en tránsito y reposo
- Auditoría completa de operaciones

### 📋 **Cumplimiento**

- Cumplimiento LGPD/GDPR
- Rastro de auditoría SOX
- Retención de logs por 7 años
- Respaldo geográfico distribuido

### 🔐 **Control de Acceso**

- Principio del menor privilegio
- MFA obligatorio para admins
- Rotación automática de claves
- Segregación de entornos