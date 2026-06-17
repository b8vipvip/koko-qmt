param(
    [string]$RepoPath = "D:\AI\koko-qmt",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$SkipInstallDeps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "⚠️ $msg" -ForegroundColor Yellow
}

function Fail($msg) {
    Write-Host ""
    Write-Host "❌ 拉取更新失败：" -ForegroundColor Red
    Write-Host $msg -ForegroundColor Red
    Write-Host ""
    exit 1
}

try {
    Write-Host "========== koko-qmt 一键安全拉取更新 ==========" -ForegroundColor Cyan

    if (!(Test-Path $RepoPath)) {
        Fail "项目目录不存在：$RepoPath"
    }

    Set-Location $RepoPath

    try {
        git --version | Out-Null
    } catch {
        Fail "未检测到 git，请先安装 Git。"
    }

    $isRepo = git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0 -or $isRepo.Trim() -ne "true") {
        Fail "当前目录不是 Git 仓库：$RepoPath"
    }

    $currentBranch = (git branch --show-current).Trim()
    if ($currentBranch -ne $Branch) {
        Fail "当前分支是 [$currentBranch]，不是目标分支 [$Branch]。请先切换到 $Branch。"
    }

    $remoteUrl = git remote get-url $Remote 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteUrl)) {
        Fail "未找到远程仓库：$Remote"
    }

    Write-Info "当前仓库：$RepoPath"
    Write-Info "当前分支：$currentBranch"
    Write-Info "远程仓库：$remoteUrl"

    Write-Host ""
    Write-Host "========== 1. 检查本地是否有未提交文件 ==========" -ForegroundColor Cyan

    $status = git status --porcelain
    if ($status) {
        Write-Host "检测到以下本地未提交或未跟踪文件：" -ForegroundColor Yellow
        Write-Host $status
        Fail "为避免覆盖本地文件，已中止拉取。请先提交、删除，或执行：git stash push -u -m `"backup before pull`""
    }

    Write-Info "本地工作区干净，没有发现会冲突的未提交文件。"

    Write-Host ""
    Write-Host "========== 2. 获取远程最新提交 ==========" -ForegroundColor Cyan

    git fetch $Remote $Branch
    if ($LASTEXITCODE -ne 0) {
        Fail "git fetch 失败，请检查网络、GitHub 权限或远程仓库地址。"
    }

    $localCommit = (git rev-parse HEAD).Trim()
    $remoteCommit = (git rev-parse "$Remote/$Branch").Trim()
    $baseCommit = (git merge-base HEAD "$Remote/$Branch").Trim()

    Write-Host "本地提交：$localCommit"
    Write-Host "远程提交：$remoteCommit"
    Write-Host "公共基点：$baseCommit"

    Write-Host ""
    Write-Host "========== 3. 判断是否可以安全快进合并 ==========" -ForegroundColor Cyan

    if ($localCommit -eq $remoteCommit) {
        Write-Info "当前已经是最新版本，无需拉取。"
    }
    elseif ($localCommit -eq $baseCommit) {
        Write-Info "检测到远程有新版本，且可以安全快进合并。"
        git merge --ff-only "$Remote/$Branch"
        if ($LASTEXITCODE -ne 0) {
            Fail "git merge --ff-only 失败。"
        }
        Write-Info "代码拉取成功。"
    }
    elseif ($remoteCommit -eq $baseCommit) {
        Fail "本地有未推送提交，远程没有包含这些提交。为避免覆盖，已中止。你可以先 git push 或手动处理。"
    }
    else {
        Fail "本地和远程分支已经分叉，不能自动拉取。请手动检查 git log --oneline --graph --all。"
    }

    Write-Host ""
    Write-Host "========== 4. 更新 Python 依赖 ==========" -ForegroundColor Cyan

    $venvPython = Join-Path $RepoPath ".venv\Scripts\python.exe"

    if ($SkipInstallDeps) {
        Write-Warn "你指定了 -SkipInstallDeps，已跳过依赖更新。"
    }
    elseif (Test-Path $venvPython) {
        & $venvPython -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Fail "依赖安装失败，请检查 requirements.txt 或网络。"
        }
        Write-Info "Python 依赖更新完成。"
    }
    else {
        Write-Warn "未找到虚拟环境 .venv，已跳过依赖更新。"
        Write-Warn "如需创建虚拟环境，请执行：py -3.10 -m venv .venv"
    }

    Write-Host ""
    Write-Host "========== 更新完成 ==========" -ForegroundColor Cyan
    Write-Info "koko-qmt 项目已安全更新完成，没有发现冲突。"
    Write-Host "你现在可以启动后端：" -ForegroundColor Cyan
    Write-Host "uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

    exit 0
}
catch {
    Fail $_.Exception.Message
}
