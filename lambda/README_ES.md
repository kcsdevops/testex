# TESTEX - Sistema de Terminación de Contratos AWS Lambda

Sistema de automatización para terminación de contratos usando AWS Lambda, DynamoDB, S3 y SES.

## 🏗️ Arquitectura

```text
Sistema TESTEX Lambda
├── contract-processor/     # Lambda para procesamiento de contratos
├── database-manager/       # Lambda para operaciones de base de datos
├── file-handler/          # Lambda para gestión de archivos
├── notification-service/   # Lambda para notificaciones
├── api-gateway/           # Lambda para endpoints de API
├── shared/                # Código compartido entre lambdas
├── infrastructure/        # Configuración AWS (CDK/CloudFormation)
├── tests/                 # Pruebas unitarias e integración
└── docs/                  # Documentación del proyecto
```

## 🚀 Funcionalidades

### Funciones Lambda Principales

- **Contract Processor**: Procesa terminaciones de contratos
- **Database Manager**: Operaciones CRUD en DynamoDB
- **File Handler**: Subida/descarga de archivos en S3
- **Notification Service**: Envío de emails vía SES
- **API Gateway**: Endpoints REST para integración

### Servicios AWS

- **AWS Lambda**: Ejecución serverless
- **DynamoDB**: Base de datos NoSQL
- **S3**: Almacenamiento de archivos
- **SES**: Servicio de email
- **API Gateway**: Endpoints REST
- **CloudWatch**: Logs y monitoreo
- **IAM**: Control de acceso

## 📦 Estructura del Proyecto

```text
/
├── src/
│   ├── lambdas/
│   │   ├── contract_processor/
│   │   │   ├── handler.py              # Manejador principal
│   │   │   └── requirements.txt        # Dependencias
│   │   ├── database_manager/
│   │   │   ├── handler.py              # Operaciones de base de datos
│   │   │   └── requirements.txt
│   │   ├── file_handler/
│   │   │   ├── handler.py              # Gestión S3
│   │   │   └── requirements.txt
│   │   ├── notification_service/
│   │   │   ├── handler.py              # Servicios de email
│   │   │   └── requirements.txt
│   │   └── api_gateway/
│   │       ├── handler.py              # Endpoints REST
│   │       └── requirements.txt
│   └── shared/
│       ├── models/                     # Modelos de datos
│       ├── utils/                      # Utilidades comunes
│       └── config/                     # Configuraciones
├── infrastructure/
│   ├── cdk_stack.py                    # Stack CDK
│   └── requirements.txt                # Dependencias CDK
├── tests/
│   ├── test_contract_processor.py      # Pruebas del procesador
│   ├── test_database_manager.py        # Pruebas de base de datos
│   └── conftest.py                     # Configuración de pruebas
├── deploy.py                           # Script de despliegue
└── requirements.txt                    # Dependencias del proyecto
```

## 🛠️ Configuración y Despliegue

### Requisitos Previos

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar AWS CLI
aws configure

# Instalar AWS CDK
npm install -g aws-cdk
```

### Despliegue de Infraestructura

```bash
# Despliegue usando script Python
python deploy.py

# O usando CDK directamente
cd infrastructure
cdk deploy
```

### Variables de Entorno

```bash
# Configuraciones obligatorias
export AWS_REGION=us-east-1
export DYNAMODB_TABLE=testex-contracts
export S3_BUCKET=testex-files
export SES_FROM_EMAIL=noreply@testex.com
```

## 🧪 Pruebas

```bash
# Ejecutar todas las pruebas
python -m pytest tests/

# Ejecutar pruebas específicas
python -m pytest tests/test_contract_processor.py

# Pruebas con cobertura
python -m pytest tests/ --cov=src/
```

## 📋 Endpoints de la API

### Contratos

```bash
# Listar contratos
GET /api/contracts

# Obtener contrato específico
GET /api/contracts/{id}

# Terminar contrato
POST /api/contracts/{id}/terminate

# Estado del contrato
GET /api/contracts/{id}/status
```

### Archivos

```bash
# Subida de archivo
POST /api/files/upload

# Descarga de archivo
GET /api/files/{file_id}

# Listar archivos
GET /api/files
```

## 🔧 Desarrollo Local

### Configuración del Entorno

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows)
.venv\Scripts\activate

# Activar entorno (Linux/Mac)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar Localmente

```bash
# Probar funciones Lambda
python test_system.py

# Ejecutar pruebas
python -m pytest

# Validar código
python -m flake8 src/
```

## 📊 Monitoreo

### CloudWatch Logs

- Logs detallados de cada función Lambda
- Métricas de rendimiento
- Alertas configurables

### Métricas Importantes

- **Duración**: Tiempo de ejecución de las funciones
- **Errores**: Cantidad de errores por función
- **Invocaciones**: Número de llamadas
- **Throttles**: Limitaciones de ejecución

## 🔒 Seguridad

### IAM Roles

- Principio del menor privilegio
- Roles específicos por función
- Acceso controlado a recursos

### Cifrado

- Datos en tránsito: HTTPS/TLS
- Datos en reposo: Cifrado S3 + DynamoDB
- Variables de entorno cifradas

## 🚨 Solución de Problemas

### Problemas Comunes

1. **Error de timeout**: Aumentar timeout de las funciones Lambda
2. **Error de memoria**: Ajustar configuración de memoria
3. **Permisos**: Verificar IAM roles y políticas
4. **Conectividad**: Validar configuraciones de VPC/subnet

### Logs Útiles

```bash
# Verificar logs de CloudWatch
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/testex"

# Visualizar logs específicos
aws logs tail "/aws/lambda/testex-contract-processor" --follow
```

## 📚 Documentación Adicional

- [Diagrama de Arquitectura](ARCHITECTURE_DIAGRAM.md)
- [Diagrama de Flujo del Sistema](FLOWCHART.md)
- [Flujo de Terminación](CONTRACT_TERMINATION_FLOW.md)
- [Diagrama Draw.io](TESTEX_Architecture.drawio)

## 🤝 Contribuyendo

1. Fork del proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de los cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la MIT License - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte y consultas:

- Email: soporte@testex.com
- Issues: [GitHub Issues](https://github.com/kcsdevops/testex/issues)
- Wiki: [Documentación Completa](https://github.com/kcsdevops/testex/wiki)

---

**TESTEX** - Sistema de Terminación de Contratos Automatizado con AWS Lambda 🚀