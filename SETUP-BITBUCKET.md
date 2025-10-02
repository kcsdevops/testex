# 🚀 Guia de Migração para Bitbucket - Projeto TESTEX

## 📋 Passos para Configurar o Bitbucket

### 1. **Criar Repositório no Bitbucket**

1. Acesse [https://bitbucket.org](https://bitbucket.org)
2. Faça login na sua conta
3. Clique em **"Create repository"**
4. Configure:
   - **Repository name**: `testex`
   - **Access level**: Private (recomendado) ou Public
   - **Include a README**: ❌ (já temos)
   - **Version control system**: Git
5. Clique em **"Create repository"**

### 2. **Configurar Credenciais de Acesso**

#### Opção A: App Passwords (Recomendado)
1. Vá para **Account Settings > App passwords**
2. Clique em **"Create app password"**
3. Configure:
   - **Label**: `TESTEX-Git-Access`
   - **Permissions**: ✅ Repositories (Read/Write)
4. **Copie a senha gerada** (não será mostrada novamente!)

#### Opção B: SSH Keys
1. Gere uma chave SSH:
```bash
ssh-keygen -t rsa -b 4096 -C "seu.email@exemplo.com"
```
2. Adicione a chave pública no Bitbucket (**Account Settings > SSH keys**)

### 3. **Comandos para Migração**

Execute os comandos abaixo **após criar o repositório**:

```powershell
# 1. Adicionar remote do Bitbucket (substitua USERNAME pela sua conta)
git remote add bitbucket https://USERNAME@bitbucket.org/USERNAME/testex.git

# 2. Fazer push para Bitbucket
git push bitbucket master

# 3. Configurar Bitbucket como origem principal (opcional)
git remote set-url origin https://USERNAME@bitbucket.org/USERNAME/testex.git

# 4. Verificar configuração
git remote -v
```

### 4. **URLs Comuns do Bitbucket**

Substitua `USERNAME` pelo seu nome de usuário:

- **HTTPS**: `https://USERNAME@bitbucket.org/USERNAME/testex.git`
- **SSH**: `git@bitbucket.org:USERNAME/testex.git`

### 5. **Configuração de Workspace/Team**

Se você estiver usando um workspace de equipe:

```powershell
# Para workspace de equipe (substitua WORKSPACE pelo nome do workspace)
git remote add bitbucket https://USERNAME@bitbucket.org/WORKSPACE/testex.git
```

### 6. **Verificação Pós-Migração**

Após a migração, execute:

```powershell
# Verificar status
git status

# Verificar remotes
git remote -v

# Verificar último commit
git log --oneline -1

# Testar push
git push bitbucket master
```

### 7. **Pipeline CI/CD no Bitbucket**

O Bitbucket Pipelines usa o arquivo `bitbucket-pipelines.yml`. Exemplo:

```yaml
# bitbucket-pipelines.yml
image: mcr.microsoft.com/powershell:latest

pipelines:
  default:
    - step:
        name: Test TESTEX Laboratory
        script:
          - cd laboratorio
          - pwsh -File Test-Laboratory.ps1 -WaitForServices -MaxWaitMinutes 5
        services:
          - docker
        
  branches:
    master:
      - step:
          name: Deploy to Production
          script:
            - echo "Deploy para produção"
            - pwsh -File TerminoContrato-Main.ps1 -Validate
```

### 8. **Migração de Issues (Opcional)**

Se você tiver issues no GitHub:

1. Export issues do GitHub (Settings > Data export)
2. Import no Bitbucket (Repository settings > Import & export)

### 9. **Configuração de Webhooks**

Para integração com outros sistemas:

1. **Repository settings > Webhooks**
2. Adicione URLs de notificação
3. Configure eventos (push, pull request, etc.)

## 🔧 Troubleshooting

### Erro de Autenticação
```powershell
# Se der erro de autenticação, use app password
git remote set-url bitbucket https://USERNAME:APP_PASSWORD@bitbucket.org/USERNAME/testex.git
```

### Erro de Certificado SSL
```powershell
# Desabilitar verificação SSL (temporário)
git config --global http.sslVerify false

# Ou configurar certificado específico
git config --global http.sslCAInfo "C:/path/to/certificate.pem"
```

### Repository não encontrado
- Verifique se o repositório foi criado
- Confirme o nome do workspace/usuário
- Verifique as permissões de acesso

## ✅ Checklist Final

- [ ] Repositório criado no Bitbucket
- [ ] App password ou SSH key configurada
- [ ] Remote do Bitbucket adicionado
- [ ] Push realizado com sucesso
- [ ] Commits e histórico preservados
- [ ] Pipeline CI/CD configurado (opcional)
- [ ] Issues migradas (opcional)
- [ ] Webhooks configurados (opcional)

---

**📞 Suporte**: Se houver problemas, forneça:
1. URL exata do repositório Bitbucket
2. Nome do workspace/usuário
3. Mensagem de erro completa
4. Output do comando `git remote -v`