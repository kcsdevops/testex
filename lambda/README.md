# TESTEX - AWS Lambda Contract Termination System

Sistema de automação para terminação de contratos usando AWS Lambda, DynamoDB, S3 e SES.

## 🏗️ Arquitetura

```
TESTEX Lambda System
├── contract-processor/     # Lambda para processamento de contratos
├── database-manager/       # Lambda para operações de banco
├── file-handler/          # Lambda para gerenciamento de arquivos
├── notification-service/   # Lambda para notificações
├── api-gateway/           # Lambda para endpoints da API
├── shared/                # Código compartilhado entre lambdas
├── infrastructure/        # Configuração AWS (CDK/CloudFormation)
├── tests/                 # Testes unitários e de integração
└── docs/                  # Documentação do projeto
```

## 🚀 Funcionalidades

### Core Lambda Functions
- **Contract Processor**: Processa terminações de contrato
- **Database Manager**: Operações CRUD no DynamoDB
- **File Handler**: Upload/download de arquivos no S3
- **Notification Service**: Envio de emails via SES
- **API Gateway**: Endpoints REST para integração

### AWS Services
- **AWS Lambda**: Execução serverless
- **DynamoDB**: Banco de dados NoSQL
- **S3**: Armazenamento de arquivos
- **SES**: Serviço de email
- **API Gateway**: Endpoints REST
- **CloudWatch**: Logs e monitoramento
- **IAM**: Controle de acesso

## 📦 Estrutura do Projeto

```
/
├── src/
│   ├── lambdas/
│   │   ├── contract_processor/
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   ├── database_manager/
│   │   ├── file_handler/
│   │   ├── notification_service/
│   │   └── api_gateway/
│   ├── shared/
│   │   ├── models/
│   │   ├── utils/
│   │   └── config/
│   └── infrastructure/
│       ├── cdk/
│       └── cloudformation/
├── tests/
├── scripts/
├── docs/
├── requirements.txt
├── serverless.yml
└── README.md
```

## 🛠️ Tecnologias

- **Python 3.11+**
- **AWS Lambda**
- **AWS CDK** para Infrastructure as Code
- **Boto3** para integração AWS
- **Pydantic** para validação de dados
- **Pytest** para testes
- **Docker** para desenvolvimento local

## 📋 Pré-requisitos

- AWS CLI configurado
- Python 3.11+
- Node.js (para AWS CDK)
- Docker (opcional, para desenvolvimento local)

## 🚀 Deployment

### Usando AWS CDK
```bash
cd infrastructure/cdk
npm install
cdk bootstrap
cdk deploy
```

### Usando Serverless Framework
```bash
npm install -g serverless
serverless deploy
```

## 🧪 Testes

```bash
# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Executar testes
pytest tests/

# Cobertura de testes
pytest --cov=src tests/
```

## 📱 API Endpoints

- `POST /contracts/terminate` - Iniciar terminação de contrato
- `GET /contracts/{id}/status` - Status da terminação
- `GET /contracts/{id}/files` - Arquivos do contrato
- `POST /contracts/{id}/notify` - Enviar notificação

## 🔧 Configuração

Variáveis de ambiente necessárias:
- `DYNAMODB_TABLE_NAME`
- `S3_BUCKET_NAME`
- `SES_FROM_EMAIL`
- `AWS_REGION`

## 📊 Monitoramento

- CloudWatch Logs para debug
- CloudWatch Metrics para performance
- X-Ray para tracing (opcional)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.