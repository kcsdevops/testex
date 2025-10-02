# TESTEX Laboratory README
# Guia completo do ambiente de laboratório

## 🏗️ Visão Geral do Laboratório

O laboratório TESTEX é um ambiente Docker completo que simula toda a infraestrutura necessária para testar o sistema de terminação de contratos. Inclui banco de dados, Active Directory, sistema de arquivos, API UMA e ferramentas de monitoramento.

## 🐳 Arquitetura dos Containers

### Serviços Principais

1. **SQL Server Express** (`sqlserver`)
   - **Imagem**: `mcr.microsoft.com/mssql/server:2019-latest`
   - **Porta**: 1433
   - **Credenciais**: sa / TestexSQL2024!
   - **Database**: TESTEX_DB (criado automaticamente)

2. **OpenLDAP** (`openldap`)
   - **Imagem**: `bitnami/openldap:latest`
   - **Portas**: 389 (LDAP), 636 (LDAPS)
   - **Credenciais**: admin / testexldap123
   - **Base DN**: dc=testex,dc=local

3. **phpLDAPadmin** (`phpldapadmin`)
   - **Imagem**: `osixia/phpldapadmin:latest`
   - **Porta**: 8080
   - **URL**: http://localhost:8080
   - **Interface web para gerenciar LDAP**

4. **Samba File Server** (`samba`)
   - **Imagem**: `dperson/samba:latest`
   - **Portas**: 139, 445 (SMB/CIFS)
   - **Compartilhamento**: \\localhost\testex
   - **Credenciais**: testuser / testpass

5. **UMA API Simulator** (`uma-api`)
   - **Imagem**: Personalizada (Flask)
   - **Porta**: 5000
   - **API Key**: testex-uma-key-2024
   - **Endpoints**: /clients, /purge, /health

6. **MailHog** (`mailhog`)
   - **Imagem**: `mailhog/mailhog:latest`
   - **Portas**: 1025 (SMTP), 8025 (Web UI)
   - **URL**: http://localhost:8025

7. **Python Environment** (`python-env`)
   - **Imagem**: Personalizada (Python 3.9)
   - **Simuladores TESTEX disponíveis**
   - **Acesso aos scripts via volume**

## 🚀 Uso do Laboratório

### Comandos Básicos

```powershell
# Iniciar todo o laboratório
.\lab.ps1 start

# Parar o laboratório
.\lab.ps1 stop

# Ver status dos serviços
.\lab.ps1 status

# Ver logs
.\lab.ps1 logs

# Reiniciar serviços
.\lab.ps1 restart

# Limpeza completa
.\lab.ps1 clean
```

### Comandos Específicos por Serviço

```powershell
# Iniciar apenas SQL Server
.\lab.ps1 start -Service sqlserver

# Ver logs da API UMA
.\lab.ps1 logs -Service uma-api

# Reiniciar OpenLDAP
.\lab.ps1 restart -Service openldap
```

## 🔧 Configuração dos Serviços

### SQL Server

**Conexão via PowerShell**:
```powershell
$connectionString = "Server=localhost,1433;Database=TESTEX_DB;User Id=sa;Password=TestexSQL2024!;"
```

**Conexão via SQLCMD**:
```bash
sqlcmd -S localhost,1433 -U sa -P TestexSQL2024! -d TESTEX_DB
```

### OpenLDAP

**Configuração para PowerShell AD Module**:
```powershell
$ldapServer = "localhost:389"
$baseDN = "dc=testex,dc=local"
$adminDN = "cn=admin,dc=testex,dc=local"
$adminPassword = "testexldap123"
```

**Interface Web**: http://localhost:8080
- **Login DN**: cn=admin,dc=testex,dc=local
- **Password**: testexldap123

### UMA API

**Base URL**: http://localhost:5000
**Headers necessários**:
```
Authorization: Bearer testex-uma-key-2024
Content-Type: application/json
```

**Endpoints principais**:
- `GET /health` - Health check
- `GET /clients/{id}` - Informações do cliente
- `POST /clients/{id}/disable` - Desabilitar cliente
- `DELETE /clients/{id}/services/{service}` - Remover serviço
- `POST /clients/{id}/purge` - Iniciar purge

### File Server

**Acesso via UNC**:
```
\\localhost\testex
Username: testuser
Password: testpass
```

**Mapeamento via PowerShell**:
```powershell
New-PSDrive -Name "T" -PSProvider FileSystem -Root "\\localhost\testex" -Credential (Get-Credential)
```

## 🧪 Testes com o Laboratório

### Teste Completo de Terminação

```powershell
# 1. Iniciar laboratório
.\lab.ps1 start

# 2. Aguardar inicialização (30-60 segundos)
Start-Sleep 60

# 3. Executar teste de terminação
cd ..\Scripts
.\Terminate-Contract.ps1 -ClienteId "CLI001" -WhatIf

# 4. Executar terminação real
.\Terminate-Contract.ps1 -ClienteId "CLI001"
```

### Validação do Sistema

```powershell
# Validar conectividade com todos os serviços
cd ..\Scripts
.\Validate-System.ps1 -TestConnections -Detailed
```

### Usar Simuladores Python

```powershell
# Executar container Python interativo
docker-compose exec python-env python /app/scripts/database_simulator.py

# Ou executar simulador específico
docker-compose exec python-env python -c "
from scripts.database_simulator import DatabaseSimulator
sim = DatabaseSimulator()
print(sim.get_client_info('CLI001'))
"
```

## 📊 Monitoramento

### Logs dos Serviços

```powershell
# Todos os logs
.\lab.ps1 logs

# Logs específicos com follow
docker-compose logs -f sqlserver
docker-compose logs -f uma-api
docker-compose logs -f openldap
```

### Status dos Containers

```powershell
# Status via lab script
.\lab.ps1 status

# Status detalhado via Docker
docker-compose ps
docker stats
```

### Recursos do Sistema

```powershell
# Uso de recursos
docker stats --no-stream

# Volumes utilizados
docker volume ls
docker system df
```

## 🔍 Solução de Problemas

### Problemas Comuns

1. **SQL Server demora para iniciar**:
   - Aguarde 60-90 segundos na primeira inicialização
   - Verifique logs: `docker-compose logs sqlserver`

2. **OpenLDAP não aceita conexões**:
   - Verifique se a porta 389 não está em uso
   - Teste conectividade: `Test-NetConnection localhost -Port 389`

3. **UMA API retorna erro 500**:
   - Verifique logs: `docker-compose logs uma-api`
   - Reconstrua o container: `docker-compose up --build uma-api`

4. **File Server não responde**:
   - Verifique se as portas 139/445 estão livres
   - No Windows, pode conflitar com SMB nativo

### Comandos de Diagnóstico

```powershell
# Verificar portas em uso
netstat -an | findstr ":1433\|:389\|:5000\|:8080"

# Testar conectividade de rede
Test-NetConnection localhost -Port 1433
Test-NetConnection localhost -Port 389
Test-NetConnection localhost -Port 5000

# Verificar espaço em disco
docker system df

# Limpar recursos não utilizados
docker system prune -f
```

## 🔄 Backup e Restore

### Backup dos Dados

```powershell
# Backup automático via Docker volumes
docker run --rm -v testex_sqlserver_data:/data -v ${PWD}/backups:/backup busybox tar czf /backup/sqlserver_backup.tar.gz -C /data .

# Backup manual do SQL Server
docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P TestexSQL2024! -Q "BACKUP DATABASE TESTEX_DB TO DISK = '/var/opt/mssql/backup/testex_backup.bak'"
```

### Restore dos Dados

```powershell
# Restore do volume
docker run --rm -v testex_sqlserver_data:/data -v ${PWD}/backups:/backup busybox tar xzf /backup/sqlserver_backup.tar.gz -C /data

# Recrear containers
.\lab.ps1 stop
.\lab.ps1 start
```

## 📈 Otimização de Performance

### Configurações Recomendadas

**Docker Desktop**:
- **RAM**: Mínimo 4GB, recomendado 8GB
- **CPU**: Mínimo 2 cores, recomendado 4 cores
- **Disk**: 20GB de espaço livre

**Windows**:
- Desabilitar antivírus em tempo real na pasta do laboratório
- Usar SSD para melhor performance de I/O
- Configurar exclusões do Windows Defender

### Monitoramento de Performance

```powershell
# Monitorar recursos em tempo real
docker stats

# Top processes nos containers
docker-compose exec sqlserver ps aux
docker-compose exec python-env htop
```

## 🔐 Segurança

### Credenciais Padrão

⚠️ **APENAS PARA DESENVOLVIMENTO**

- **SQL Server**: sa / TestexSQL2024!
- **LDAP**: admin / testexldap123  
- **SMB**: testuser / testpass
- **UMA API**: testex-uma-key-2024

### Recomendações

1. **Não usar em produção** com essas credenciais
2. **Isolar rede** do laboratório
3. **Firewall** bloquear acesso externo
4. **Monitorar** acessos e logs

---

**TESTEX Laboratory v1.0**  
Ambiente completo para desenvolvimento e testes do sistema de terminação de contratos.