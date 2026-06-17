param(
    [string]$RepoPath = "D:\AI\koko-qmt",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$SkipInstallDeps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail($msg) {
    Write-Host ""
    Write-Host "❌ 安全拉取失败：" -ForegroundColor Red
    Write-Host $msg -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Ok($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

try {
    Write-Host "========== koko-qmt 安全拉取远程更新 ==========" -ForegroundColor Cyan

    if (!(Test-Path $RepoPath)) {
        Fail "项目目录不存在：$RepoPath"
    }

    Set-Location $RepoPath

    git --version | Out-Null

    $isRepo = git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0 -or $isRepo.Trim() -ne "true") {
        Fail "当前目录不是 Git 仓库：$RepoPath"
    }

    $currentBranch = (git branch --show-current).Trim()
    if ($currentBranch -ne $Branch) {
        Fail "当前分支是 [$currentBranch]，不是目标分支 [$Branch]。"
    }

    Write-Host ""
    Write-Host "========== 1. 检查本地工作区 ==========" -ForegroundColor Cyan

    $status = git status --porcelain
    if ($status) {
        Write-Host "检测到本地未提交或未跟踪文件：" -ForegroundColor Yellow
        Write-Host $status
        Fail "为避免覆盖本地文件，已中止。请先提交、删除，或执行 sync_repo.ps1 处理。"
    }

    Ok "本地工作区干净。"

    Write-Host ""
    Write-Host "========== 2. 获取远程最新状态 ==========" -ForegroundColor Cyan

    git fetch $Remote $Branch
    if ($LASTEXITCODE -ne 0) {
        Fail "git fetch 失败，请检查网络、GitHub 权限或远程仓库地址。"
    }

    $localCommit = (git rev-parse HEAD).Trim()
    $remoteCommit = (git rev-parse "$Remote/$Branch").Trim()
    $baseCommit = (git merge-base HEAD "$Remote/$Branch").Trim()

    if ($localCommit -eq $remoteCommit) {
        Ok "当前已经是最新版本，无需拉取。"
    }
    elseif ($localCommit -eq $baseCommit) {
        git merge --ff-only "$Remote/$Branch"
        if ($LASTEXITCODE -ne 0) {
            Fail "快进合并失败。"
        }
        Ok "远程更新已安全拉取。"
    }
    elseif ($remoteCommit -eq $baseCommit) {
        Fail "本地有未推送提交，不能直接拉取。请先执行 sync_repo.ps1 推送。"
    }
    else {
        Fail "本地和远程已经分叉，不能自动处理。请手动检查 git log --oneline --graph --all。"
    }

    if (!$SkipInstallDeps) {
        $venvPython = Join-Path $RepoPath ".venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            Write-Host ""
            Write-Host "========== 3. 更新依赖 ==========" -ForegroundColor Cyan
            & $venvPython -m pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Fail "依赖安装失败。"
            }
            Ok "依赖更新完成。"
        }
        else {
            Write-Host "⚠️ 未找到 .venv，跳过依赖安装。" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Ok "koko-qmt 拉取更新完成，没有发现冲突。"
}
catch {
    Fail $_.Exception.Message
}
