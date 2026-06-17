param(
    [string]$RepoPath = "D:\AI\koko-qmt",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$Message = "",
    [switch]$NoPush,
    [switch]$SkipPull
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail($msg) {
    Write-Host ""
    Write-Host "❌ 同步失败：" -ForegroundColor Red
    Write-Host $msg -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Ok($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

function HasConflictMarkers() {
    $files = git ls-files
    foreach ($file in $files) {
        if (Test-Path $file) {
            # 只检测真正的 Git 冲突标记：行首出现 <<<<<<<、=======、>>>>>>>
            # 避免把普通分隔线、日志、中文提示误判为冲突。
            $matched = Select-String -Path $file -Pattern '^\s*(<{7}|={7}|>{7})(\s|$)' -Quiet -ErrorAction SilentlyContinue
            if ($matched) {
                return $true
            }
        }
    }
    return $false
}

try {
    Write-Host "========== koko-qmt 本地/远程安全同步 ==========" -ForegroundColor Cyan

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

    if (HasConflictMarkers) {
        Fail "检测到疑似 Git 冲突标记 <<<<<<< ======= >>>>>>>，请先手动处理。"
    }

    Write-Host ""
    Write-Host "========== 1. 获取远程状态 ==========" -ForegroundColor Cyan

    git fetch $Remote $Branch
    if ($LASTEXITCODE -ne 0) {
        Fail "git fetch 失败。"
    }

    $localCommit = (git rev-parse HEAD).Trim()
    $remoteCommit = (git rev-parse "$Remote/$Branch").Trim()
    $baseCommit = (git merge-base HEAD "$Remote/$Branch").Trim()

    $dirty = git status --porcelain

    if (!$SkipPull) {
        if ($localCommit -eq $remoteCommit) {
            Ok "本地和远程提交一致。"
        }
        elseif ($localCommit -eq $baseCommit) {
            if ($dirty) {
                Write-Host "检测到远程有新提交，同时本地有未提交改动，开始自动 stash..." -ForegroundColor Yellow

                git stash push -u -m "auto backup before sync $(Get-Date -Format 'yyyyMMdd_HHmmss')"
                if ($LASTEXITCODE -ne 0) {
                    Fail "自动 stash 失败。"
                }

                git merge --ff-only "$Remote/$Branch"
                if ($LASTEXITCODE -ne 0) {
                    Fail "拉取远程更新失败。你的本地改动已暂存在 git stash。"
                }

                git stash pop
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "⚠️ stash pop 出现冲突，请执行 git status 查看冲突文件。" -ForegroundColor Yellow
                    Fail "远程更新与本地改动发生冲突，已停止自动提交。"
                }

                Ok "远程更新已拉取，本地改动已恢复。"
            }
            else {
                git merge --ff-only "$Remote/$Branch"
                if ($LASTEXITCODE -ne 0) {
                    Fail "快进合并失败。"
                }
                Ok "远程更新已安全拉取。"
            }
        }
        elseif ($remoteCommit -eq $baseCommit) {
            Ok "本地领先远程，准备提交/推送。"
        }
        else {
            Fail "本地和远程已经分叉，不能自动同步。请手动检查 git log --oneline --graph --all。"
        }
    }

    if (HasConflictMarkers) {
        Fail "检测到冲突标记，请先处理后再同步。"
    }

    Write-Host ""
    Write-Host "========== 2. 检查本地改动 ==========" -ForegroundColor Cyan

    $status = git status --porcelain
    if ($status) {
        Write-Host "待提交文件：" -ForegroundColor Cyan
        Write-Host $status

        if ([string]::IsNullOrWhiteSpace($Message)) {
            $Message = Read-Host "请输入本次提交说明，例如 chore: update scripts"
            if ([string]::IsNullOrWhiteSpace($Message)) {
                Fail "提交说明不能为空。"
            }
        }

        git add -A
        if ($LASTEXITCODE -ne 0) {
            Fail "git add 失败。"
        }

        git commit -m $Message
        if ($LASTEXITCODE -ne 0) {
            Fail "git commit 失败。"
        }

        Ok "本地改动已提交。"
    }
    else {
        Ok "没有本地改动需要提交。"
    }

    if (!$NoPush) {
        Write-Host ""
        Write-Host "========== 3. 推送到 GitHub ==========" -ForegroundColor Cyan

        git push $Remote $Branch
        if ($LASTEXITCODE -ne 0) {
            Fail "git push 失败，可能远程有新提交。请先重新运行本脚本。"
        }

        Ok "已推送到 GitHub：$Remote/$Branch"
    }
    else {
        Write-Host "⚠️ 你指定了 -NoPush，已跳过推送。" -ForegroundColor Yellow
    }

    Write-Host ""
    Ok "本地和远程同步完成。"
}
catch {
    Fail $_.Exception.Message
}

