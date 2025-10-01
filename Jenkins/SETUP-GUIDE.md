# GUIA DE CONFIGURAÇÃO DO JENKINS PARA TESTEX

## 1. Pré-requisitos

### Plugins Necessários:
- Pipeline
- PowerShell Plugin
- Email Extension Plugin
- Workspace Cleanup Plugin
- Parameterized Trigger Plugin

### Configurações do Jenkins:
- Instalar PowerShell Plugin
- Configurar credenciais para SQL Server
- Configurar credenciais para Active Directory
- Configurar SMTP para notificações

## 2. Criação do Job

1. **Novo Item** → **Pipeline**
2. **Nome**: `TESTEX-TerminacaoContrato`
3. **Configuração**:
   - **Pipeline Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/empresa/testex.git`
   - **Script Path**: `Jenkins/Jenkinsfile`

## 3. Configuração de Credenciais

### SQL Server:
```
ID: sql-server-credentials
Type: Username with password
Username: sa
Password: [senha-do-sql]
```

### Active Directory:
```
ID: ad-credentials  
Type: Username with password
Username: svc-automacao@empresa.local
Password: [senha-do-ad]
```

### UMA System:
```
ID: uma-api-key
Type: Secret text
Secret: [api-key-do-uma]
```

## 4. Configuração de Notificações

### Email Configuration:
- **SMTP Server**: mail.empresa.com
- **Port**: 587
- **Use SSL**: Yes
- **Username**: automacao@empresa.com
- **Password**: [senha-do-email]

## 5. Execução

### Parâmetros do Pipeline:
- **CLIENTE_ID**: ID do cliente (obrigatório)
- **OPERACAO**: TERMINO_CONTRATO ou VALIDACAO_PURGE
- **EXECUTAR_BACKUP**: true/false

### Exemplo de Execução:
```
CLIENTE_ID: CL001
OPERACAO: TERMINO_CONTRATO
EXECUTAR_BACKUP: true
```

## 6. Monitoramento

### Logs Disponíveis:
- Console Output do Jenkins
- Logs da aplicação em `Logs/`
- Relatórios em `Reports/`

### Notificações:
- Email de sucesso/falha
- Slack (se configurado)
- Dashboard do Jenkins

## 7. Troubleshooting

### Problemas Comuns:
1. **PowerShell Execution Policy**: Configurar Bypass
2. **Credenciais**: Verificar se estão corretas
3. **Conectividade**: Testar conexões com SQL/AD
4. **Permissões**: Verificar permissões de arquivo

### Scripts de Diagnóstico:
```powershell
# Testar conectividade
.\Test-SystemValidation.ps1

# Verificar configurações
.\Setup-Credentials.ps1 -Validate
```