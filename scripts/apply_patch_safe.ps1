param(
    [Parameter(Mandatory=$true)]
    [string]$PatchFile,

    [string]$RepoPath = "D:\AI\koko-qmt",

    [string]$Remote = "origin",

    [string]$Branch = "main",

    [string]$Message = "",

    [switch]$NoCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail($msg) {
    Write-Host ""
    Write-Host "❌ 应用补丁失败：" -ForegroundColor Red
    Write-Host $msg -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Ok($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

try {
    Write-Host "========== koko-qmt 安全应用 patch ==========" -ForegroundColor Cyan

    if (!(Test-Path $RepoPath)) {
        Fail "项目目录不存在：$RepoPath"
    }

    Set-Location $RepoPath

    if (!(Test-Path $PatchFile)) {
        Fail "补丁文件不存在：$PatchFile"
    }

    $currentBranch = (git branch --show-current).Trim()
    if ($currentBranch -ne $Branch) {
        Fail "当前分支是 [$currentBranch]，不是目标分支 [$Branch]。"
    }

    Write-Host ""
    Write-Host "========== 1. 检查本地是否干净 ==========" -ForegroundColor Cyan

    $status = git status --porcelain
    if ($status) {
        Write-Host $status
        Fail "本地已有未提交改动。为避免混乱，请先执行 sync_repo.ps1 或手动处理。"
    }

    Write-Host ""
    Write-Host "========== 2. 检查远程是否有新版本 ==========" -ForegroundColor Cyan

    git fetch $Remote $Branch
    if ($LASTEXITCODE -ne 0) {
        Fail "git fetch 失败。"
    }

    $localCommit = (git rev-parse HEAD).Trim()
    $remoteCommit = (git rev-parse "$Remote/$Branch").Trim()
    $baseCommit = (git merge-base HEAD "$Remote/$Branch").Trim()

    if ($localCommit -ne $remoteCommit) {
        if ($localCommit -eq $baseCommit) {
            Fail "远程有新版本，请先执行 scripts\safe_pull_update.ps1 拉取后再应用补丁。"
        }
        else {
            Fail "本地与远程不是同一状态，请先同步后再应用补丁。"
        }
    }

    Write-Host ""
    Write-Host "========== 3. 预检查 patch ==========" -ForegroundColor Cyan

    git apply --check $PatchFile
    if ($LASTEXITCODE -ne 0) {
        Fail "patch 预检查失败，可能文件内容不匹配或已有修改。"
    }

    Write-Host ""
    Write-Host "========== 4. 应用 patch ==========" -ForegroundColor Cyan

    git apply --whitespace=fix $PatchFile
    if ($LASTEXITCODE -ne 0) {
        Fail "patch 应用失败。"
    }

    Ok "patch 已应用。"

    git diff --stat

    if (!$NoCommit) {
        if ([string]::IsNullOrWhiteSpace($Message)) {
            $Message = Read-Host "请输入本次提交说明，例如 fix: update db config"
            if ([string]::IsNullOrWhiteSpace($Message)) {
                Fail "提交说明不能为空。"
            }
        }

        git add -A
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) {
            Fail "提交失败。"
        }

        Ok "patch 改动已提交。"
        Write-Host "如需推送到 GitHub，请执行：" -ForegroundColor Cyan
        Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\sync_repo.ps1 -Message `"$Message`""
    }
    else {
        Write-Host "⚠️ 你指定了 -NoCommit，patch 已应用但未提交。" -ForegroundColor Yellow
    }
}
catch {
    Fail $_.Exception.Message
}
