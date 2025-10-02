# TESTEX - Sistema de Terminação de Contratos AWS Lambda

Sistema de automação para terminação de contratos usando AWS Lambda, DynamoDB, S3 e SES.

## 🏗️ Arquitetura

```
Sistema TESTEX Lambda
├── contract-processor/     # Lambda para processamento de contratos
├── database-manager/       # Lambda para operações de banco de dados
├── file-handler/          # Lambda para gerenciamento de arquivos
├── notification-service/   # Lambda para notificações
├── api-gateway/           # Lambda para endpoints da API
├── shared/                # Código compartilhado entre lambdas
├── infrastructure/        # Configuração AWS (CDK/CloudFormation)
├── tests/                 # Testes unitários e de integração
└── docs/                  # Documentação do projeto
```

## 🚀 Funcionalidades

### Funções Lambda Principais

- **Contract Processor**: Processa terminações de contratos
- **Database Manager**: Operações CRUD no DynamoDB
- **File Handler**: Upload/download de arquivos no S3
- **Notification Service**: Envio de emails via SES
- **API Gateway**: Endpoints REST para integração

### Serviços AWS

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
│   │   │   ├── handler.py              # Manipulador principal
│   │   │   └── requirements.txt        # Dependências
│   │   ├── database_manager/
│   │   │   ├── handler.py              # Operações de banco
│   │   │   └── requirements.txt
│   │   ├── file_handler/
│   │   │   ├── handler.py              # Gerenciamento S3
│   │   │   └── requirements.txt
│   │   ├── notification_service/
│   │   │   ├── handler.py              # Serviços de email
│   │   │   └── requirements.txt
│   │   └── api_gateway/
│   │       ├── handler.py              # Endpoints REST
│   │       └── requirements.txt
│   └── shared/
│       ├── models/                     # Modelos de dados
│       ├── utils/                      # Utilitários comuns
│       └── config/                     # Configurações
├── infrastructure/
│   ├── cdk_stack.py                    # Stack CDK
│   └── requirements.txt                # Dependências CDK
├── tests/
│   ├── test_contract_processor.py      # Testes do processador
│   ├── test_database_manager.py        # Testes do banco
│   └── conftest.py                     # Configuração de testes
├── deploy.py                           # Script de deploy
└── requirements.txt                    # Dependências do projeto
```

## 🛠️ Configuração e Deploy

### Pré-requisitos

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar AWS CLI
aws configure

# Instalar AWS CDK
npm install -g aws-cdk
```

### Deploy da Infraestrutura

```bash
# Deploy usando script Python
python deploy.py

# Ou usando CDK diretamente
cd infrastructure
cdk deploy
```

### Variáveis de Ambiente

```bash
# Configurações obrigatórias
export AWS_REGION=us-east-1
export DYNAMODB_TABLE=testex-contracts
export S3_BUCKET=testex-files
export SES_FROM_EMAIL=noreply@testex.com
```

## 🧪 Testes

```bash
# Executar todos os testes
python -m pytest tests/

# Executar testes específicos
python -m pytest tests/test_contract_processor.py

# Testes com cobertura
python -m pytest tests/ --cov=src/
```

## 📋 Endpoints da API

### Contratos

```bash
# Listar contratos
GET /api/contracts

# Obter contrato específico
GET /api/contracts/{id}

# Terminar contrato
POST /api/contracts/{id}/terminate

# Status do contrato
GET /api/contracts/{id}/status
```

### Arquivos

```bash
# Upload de arquivo
POST /api/files/upload

# Download de arquivo
GET /api/files/{file_id}

# Listar arquivos
GET /api/files
```

## 🔧 Desenvolvimento Local

### Configuração do Ambiente

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente (Windows)
.venv\Scripts\activate

# Ativar ambiente (Linux/Mac)
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Executar Localmente

```bash
# Testar funções Lambda
python test_system.py

# Executar testes
python -m pytest

# Validar código
python -m flake8 src/
```

## 📊 Monitoramento

### CloudWatch Logs

- Logs detalhados de cada função Lambda
- Métricas de performance
- Alertas configuráveis

### Métricas Importantes

- **Duração**: Tempo de execução das funções
- **Erros**: Quantidade de erros por função
- **Invocações**: Número de chamadas
- **Throttles**: Limitações de execução

## 🔒 Segurança

### IAM Roles

- Princípio do menor privilégio
- Roles específicas por função
- Acesso controlado aos recursos

### Criptografia

- Dados em trânsito: HTTPS/TLS
- Dados em repouso: S3 + DynamoDB encryption
- Variáveis de ambiente criptografadas

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de timeout**: Aumentar timeout das funções Lambda
2. **Erro de memória**: Ajustar configuração de memória
3. **Permissões**: Verificar IAM roles e policies
4. **Conectividade**: Validar configurações de VPC/subnet

### Logs úteis

```bash
# Verificar logs do CloudWatch
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/testex"

# Visualizar logs específicos
aws logs tail "/aws/lambda/testex-contract-processor" --follow
```

## 📚 Documentação Adicional

- [Diagrama de Arquitetura](ARCHITECTURE_DIAGRAM.md)
- [Fluxograma do Sistema](FLOWCHART.md)
- [Fluxo de Terminação](CONTRACT_TERMINATION_FLOW.md)
- [Diagrama Draw.io](TESTEX_Architecture.drawio)

## 🤝 Contribuindo

1. Fork do projeto
2. Criar branch para feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit das mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para o branch (`git push origin feature/nova-funcionalidade`)
5. Criar Pull Request

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- Email: suporte@testex.com
- Issues: [GitHub Issues](https://github.com/kcsdevops/testex/issues)
- Wiki: [Documentação Completa](https://github.com/kcsdevops/testex/wiki)

---

**TESTEX** - Sistema de Terminação de Contratos Automatizado com AWS Lambda 🚀