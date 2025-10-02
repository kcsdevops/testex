# README - Testes de Conectividade do Laboratório TESTEX

## 🧪 Sistema de Testes de Conectividade

Este sistema fornece testes abrangentes para verificar a conectividade e disponibilidade de todos os serviços do laboratório TESTEX, incluindo banco de dados, Active Directory simulado, APIs, e interfaces web.

## 📁 Arquivos Principais

### `Test-Laboratory.ps1`
Script principal de testes de conectividade com funcionalidades completas:

- **Testes de Infraestrutura**: Docker Engine e Docker Compose
- **Testes de Container**: Status e health checks de todos os containers
- **Testes de Rede**: Conectividade TCP para todas as portas de serviço
- **Testes de Serviço**: Validação específica de SQL Server, LDAP, UMA API
- **Testes de Interface**: Verificação das interfaces web (phpLDAPadmin, MailHog)

### `lab.ps1` (atualizado)
Script de gerenciamento do laboratório com comando de teste integrado:
- Comando `test` adicionado para executar testes de conectividade
- Integração com o script `Test-Laboratory.ps1`

### `demo-connectivity.ps1`
Demonstração interativa do sistema de testes mostrando:
- Verificação de status do laboratório
- Execução de testes completos
- Início automatizado com validação
- Opções avançadas de teste

## 🚀 Como Usar

### Teste Rápido
```powershell
# Via comando integrado do lab
.\lab.ps1 test

# Ou diretamente
.\Test-Laboratory.ps1
```

### Teste Detalhado
```powershell
.\Test-Laboratory.ps1 -Detailed
```

### Teste com Espera por Serviços
```powershell
.\Test-Laboratory.ps1 -WaitForServices -MaxWaitMinutes 5 -Detailed
```

### Teste com Correção Automática
```powershell
.\Test-Laboratory.ps1 -FixIssues -Detailed
```

### Demonstração Completa
```powershell
.\demo-connectivity.ps1
```

## 📊 Tipos de Teste

### 1. Testes de Infraestrutura
- ✅ Docker Engine disponível e funcionando
- ✅ Docker Compose instalado e operacional

### 2. Testes de Container
- ✅ Status de todos os containers (running/stopped)
- ✅ Health checks dos containers que possuem
- ✅ Identificação de containers problemáticos

### 3. Testes de Conectividade de Rede
- ✅ SQL Server (porta 1433)
- ✅ OpenLDAP (porta 389)
- ✅ UMA API (porta 5000)
- ✅ File Server Samba (porta 445)
- ✅ MailHog SMTP (porta 1025)
- ✅ phpLDAPadmin Web (porta 8080)
- ✅ MailHog Web UI (porta 8025)

### 4. Testes de Serviço Específico

#### SQL Server
- ✅ Conexão com credenciais (sa/TestexSQL2024!)
- ✅ Execução de query de teste (SELECT @@VERSION)
- ✅ Validação de módulos SQL disponíveis

#### OpenLDAP (Active Directory Simulado)
- ✅ Conexão LDAP básica
- ✅ Busca no Base DN (dc=testex,dc=local)
- ✅ Validação de credenciais administrativas

#### UMA API
- ✅ Endpoint de health check
- ✅ Autenticação com API key
- ✅ Validação de status dos clientes

### 5. Testes de Interface Web
- ✅ phpLDAPadmin (http://localhost:8080)
- ✅ MailHog Web UI (http://localhost:8025)
- ✅ Validação de código HTTP 200

## 🎯 Cenários de Uso

### Desenvolvimento
```powershell
# Iniciar laboratório e aguardar todos os serviços
.\lab.ps1 start
.\Test-Laboratory.ps1 -WaitForServices -Detailed
```

### Debugging
```powershell
# Identificar problemas específicos
.\Test-Laboratory.ps1 -Detailed -FixIssues
```

### Validação de Deploy
```powershell
# Teste completo após atualizações
.\Test-Laboratory.ps1 -WaitForServices -MaxWaitMinutes 10 -Detailed
```

### Monitoramento
```powershell
# Verificação rápida de status
.\lab.ps1 test
```

## 📈 Interpretação dos Resultados

### ✅ Sucesso
- Todos os testes passaram
- Laboratório totalmente funcional
- Exibição de endpoints disponíveis

### ⚠️ Parcial
- Alguns serviços apresentam problemas
- Identificação específica dos problemas
- Sugestões de correção

### ❌ Falha
- Problemas críticos identificados
- Docker não disponível ou containers não funcionando
- Instruções para resolução

## 🔧 Solução de Problemas

### Docker não está rodando
```powershell
# Inicie o Docker Desktop manualmente
# Ou via PowerShell (requer privilégios administrativos)
Start-Service docker
```

### Containers não inicializam
```powershell
# Restart com rebuild
.\lab.ps1 stop
.\lab.ps1 start --build
```

### Portas em uso
```powershell
# Identificar processos usando as portas
netstat -ano | findstr :1433
netstat -ano | findstr :389
netstat -ano | findstr :5000
```

### Problemas de conectividade
```powershell
# Teste de rede básico
Test-NetConnection localhost -Port 1433
Test-NetConnection localhost -Port 389
```

## 🌐 Endpoints e Credenciais

### SQL Server
- **Host**: localhost:1433
- **Usuário**: sa
- **Senha**: TestexSQL2024!
- **Database**: master (padrão)

### OpenLDAP
- **Host**: localhost:389
- **Admin DN**: cn=admin,dc=testex,dc=local
- **Senha**: testexldap123
- **Base DN**: dc=testex,dc=local

### UMA API
- **Host**: http://localhost:5000
- **Health**: http://localhost:5000/health
- **API Key**: testex-uma-key-2024

### File Server (Samba)
- **Share**: \\localhost\testex
- **Usuário**: testuser
- **Senha**: testpass

### MailHog
- **SMTP**: localhost:1025
- **Web UI**: http://localhost:8025

### phpLDAPadmin
- **Web UI**: http://localhost:8080
- **Login**: cn=admin,dc=testex,dc=local / testexldap123

## 🚀 Integração com CI/CD

O script de testes pode ser integrado em pipelines de CI/CD:

```yaml
# Jenkins Pipeline Example
stage('Test Laboratory') {
    steps {
        script {
            powershell '''
                cd laboratorio
                .\\Test-Laboratory.ps1 -WaitForServices -MaxWaitMinutes 5
                if ($LASTEXITCODE -ne 0) {
                    throw "Laboratory connectivity tests failed"
                }
            '''
        }
    }
}
```

## 📝 Logs e Debugging

### Habilitar logs detalhados
```powershell
.\Test-Laboratory.ps1 -Detailed -Verbose
```

### Verificar logs dos containers
```powershell
.\lab.ps1 logs                    # Todos os serviços
.\lab.ps1 logs -Service sqlserver # Serviço específico
```

### Debug de conexões específicas
```powershell
# SQL Server
sqlcmd -S localhost,1433 -U sa -P TestexSQL2024! -Q "SELECT @@SERVERNAME"

# LDAP
# Requires AD module or ldp.exe tool

# UMA API
Invoke-RestMethod -Uri "http://localhost:5000/health" -Headers @{'Authorization'='Bearer testex-uma-key-2024'}
```

---

**✨ Sistema desenvolvido para o projeto TESTEX - Automação de Término de Contratos**

Este sistema de testes garante que todos os componentes do laboratório estejam funcionando corretamente antes da execução dos processos de automação, proporcionando maior confiabilidade e facilidade de debugging.