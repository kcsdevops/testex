# Script de Migração para Bitbucket - Projeto TESTEX
# Execute este script após criar o repositório no Bitbucket

param(
    [Parameter(Mandatory=$true)]
    [string]$BitbucketUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceName = "",
    
    [Parameter(Mandatory=$false)]
    [string]$RepositoryName = "testex",
    
    [Parameter(Mandatory=$false)]
    [string]$AppPassword = "",
    
    [switch]$SetAsOrigin = $false,
    
    [switch]$TestConnection = $true
)

Write-Host "🚀 MIGRAÇÃO TESTEX PARA BITBUCKET" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Função para validar se estamos no diretório correto
function Test-TestexRepository {
    if (-not (Test-Path "COMMANDS.ps1")) {
        Write-Host "❌ Erro: Execute este script no diretório raiz do projeto TESTEX" -ForegroundColor Red
        Write-Host "   Diretório atual: $(Get-Location)" -ForegroundColor Yellow
        Write-Host "   Procurando por: COMMANDS.ps1" -ForegroundColor Yellow
        return $false
    }
    return $true
}

# Função para construir URL do Bitbucket
function Get-BitbucketUrl {
    param($Username, $WorkspaceName, $RepositoryName, $AppPassword)
    
    $workspace = if ($WorkspaceName) { $WorkspaceName } else { $Username }
    
    if ($AppPassword) {
        return "https://${Username}:${AppPassword}@bitbucket.org/${workspace}/${RepositoryName}.git"
    } else {
        return "https://${Username}@bitbucket.org/${workspace}/${RepositoryName}.git"
    }
}

# Validações iniciais
if (-not (Test-TestexRepository)) {
    exit 1
}

# Obter informações se não fornecidas
if (-not $AppPassword) {
    Write-Host "⚠️  App Password não fornecida." -ForegroundColor Yellow
    Write-Host "   Você pode fornecer via parâmetro -AppPassword ou será solicitada durante o push" -ForegroundColor Yellow
    Write-Host ""
}

# Construir URL do Bitbucket
$bitbucketUrl = Get-BitbucketUrl -Username $BitbucketUsername -WorkspaceName $WorkspaceName -RepositoryName $RepositoryName -AppPassword $AppPassword

Write-Host "📋 CONFIGURAÇÃO:" -ForegroundColor Cyan
Write-Host "   Username: $BitbucketUsername" -ForegroundColor White
Write-Host "   Workspace: $(if ($WorkspaceName) { $WorkspaceName } else { $BitbucketUsername })" -ForegroundColor White
Write-Host "   Repository: $RepositoryName" -ForegroundColor White
Write-Host "   URL: $($bitbucketUrl -replace ':.*@', ':***@')" -ForegroundColor White
Write-Host ""

# Verificar status atual do git
Write-Host "🔍 Verificando repositório atual..." -ForegroundColor Cyan
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "⚠️  Há alterações não commitadas:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $commit = Read-Host "Deseja fazer commit das alterações? (s/N)"
    if ($commit -eq 's' -or $commit -eq 'S') {
        git add .
        git commit -m "chore: Preparação para migração para Bitbucket"
        Write-Host "✅ Commit realizado" -ForegroundColor Green
    }
}

# Verificar remotes atuais
Write-Host "🔗 Remotes atuais:" -ForegroundColor Cyan
git remote -v
Write-Host ""

# Remover remote bitbucket se já existir
$existingBitbucket = git remote get-url bitbucket 2>$null
if ($existingBitbucket) {
    Write-Host "🔄 Removendo remote bitbucket existente..." -ForegroundColor Yellow
    git remote remove bitbucket
}

# Adicionar remote do Bitbucket
Write-Host "➕ Adicionando remote do Bitbucket..." -ForegroundColor Cyan
try {
    git remote add bitbucket $bitbucketUrl
    Write-Host "✅ Remote bitbucket adicionado com sucesso" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao adicionar remote: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Testar conexão se solicitado
if ($TestConnection) {
    Write-Host "🌐 Testando conexão com Bitbucket..." -ForegroundColor Cyan
    try {
        $fetchResult = git ls-remote bitbucket 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Conexão com Bitbucket estabelecida" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Teste de conexão falhou - isso pode ser normal se o repositório estiver vazio" -ForegroundColor Yellow
            Write-Host "   Resultado: $fetchResult" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠️  Não foi possível testar a conexão" -ForegroundColor Yellow
    }
}

# Fazer push para Bitbucket
Write-Host "⬆️  Fazendo push para Bitbucket..." -ForegroundColor Cyan
try {
    git push bitbucket master
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Push para Bitbucket realizado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "❌ Erro durante o push. Verifique as credenciais e a existência do repositório." -ForegroundColor Red
        Write-Host "💡 Dicas:" -ForegroundColor Yellow
        Write-Host "   1. Verifique se o repositório foi criado no Bitbucket" -ForegroundColor White
        Write-Host "   2. Confirme o App Password ou configure SSH" -ForegroundColor White
        Write-Host "   3. Verifique o nome do workspace/usuário" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "❌ Erro durante o push: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Configurar Bitbucket como origem principal se solicitado
if ($SetAsOrigin) {
    Write-Host "🔄 Configurando Bitbucket como remote origin..." -ForegroundColor Cyan
    
    # Backup do remote origin atual
    $currentOrigin = git remote get-url origin
    git remote rename origin github-backup
    git remote rename bitbucket origin
    
    Write-Host "✅ Bitbucket configurado como remote principal" -ForegroundColor Green
    Write-Host "   GitHub salvo como 'github-backup': $currentOrigin" -ForegroundColor Gray
}

# Verificar configuração final
Write-Host "`n📊 CONFIGURAÇÃO FINAL:" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
git remote -v

Write-Host "`n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Verifique o repositório no Bitbucket" -ForegroundColor White
Write-Host "   2. Configure Bitbucket Pipelines (opcional)" -ForegroundColor White
Write-Host "   3. Atualize documentação com nova URL" -ForegroundColor White
Write-Host "   4. Notifique a equipe sobre a mudança" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Links úteis:" -ForegroundColor Cyan
$workspace = if ($WorkspaceName) { $WorkspaceName } else { $BitbucketUsername }
Write-Host "   Repository: https://bitbucket.org/$workspace/$RepositoryName" -ForegroundColor White
Write-Host "   Settings: https://bitbucket.org/$workspace/$RepositoryName/admin" -ForegroundColor White
Write-Host "   Pipelines: https://bitbucket.org/$workspace/$RepositoryName/addon/pipelines/home" -ForegroundColor White