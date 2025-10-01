# Projeto TESTEX - Automação de Terminação de Contratos

## Descrição
Sistema de automação para terminação de contratos com integração ao Active Directory, UMA e sistemas de arquivos.

## Estrutura do Projeto

### 📁 laboratorio/
Ambiente de desenvolvimento e testes isolado do código de produção.

**Arquivos principais:**
- `start-demo.ps1` - Script de inicialização do ambiente de demonstração
- `lab_simulator_simple.py` - Simulador interativo dos processos de automação
- `docker-compose-demo.yml` - Configuração Docker simplificada

**Como usar o laboratório:**
```powershell
cd laboratorio
./start-demo.ps1
```

### 🎯 Funcionalidades
- ✅ Simulação de terminação de contratos (7 etapas)
- ✅ Validação de processos de purge (5 etapas)  
- ✅ Teste de conectividade com sistemas
- ✅ Interface interativa em português
- ✅ Logs detalhados de cada operação

### 🐳 Docker Demo
O ambiente de demonstração utiliza Docker para simular:
- Container Python com simuladores
- Logs em tempo real
- Testes de conectividade

### 📋 Requisitos
- Docker Desktop
- PowerShell 5.1+
- Python 3.11+ (para execução local)

### 🚀 Início Rápido
1. Clone o repositório
2. Execute `laboratorio/start-demo.ps1`
3. Siga as instruções do simulador interativo
4. Teste as funcionalidades de terminação e purge

### 📖 Documentação
- `laboratorio/README.md` - Guia detalhado do laboratório
- Logs disponíveis em tempo real durante execução

### 🔧 Desenvolvimento
Este projeto separa claramente:
- **Produção**: Código para entrega ao cliente (não incluído neste repo)  
- **Laboratório**: Ambiente de testes e demonstração

### ✨ Características
- Interface bilíngue (Português/Espanhol)
- Simulação completa dos processos
- Ambiente isolado para testes
- Documentação humanizada