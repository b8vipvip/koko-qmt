param(
    [string]$RepoPath = "D:\AI\koko-qmt",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$Message = "",
    [switch]$NoPush,
    [switch]$SkipInstallDeps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ok($msg) {
    Write-Host "✅ $msg" -ForegroundColor Green
}

function Warn($msg) {
    Write-Host "⚠️ $msg" -ForegroundColor Yellow
}

function Fail($msg) {
    Write-Host ""
    Write-Host "❌ 同步失败：" -ForegroundColor Red
    Write-Host $msg -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Run-Git($argsLine) {
    Write-Host "git $argsLine" -ForegroundColor DarkGray
    Invoke-Expression "git $argsLine"
    if ($LASTEXITCODE -ne 0) {
        Fail "Git 命令执行失败：git $argsLine"
    }
}

function Ensure-GitRepo() {
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
        Fail "当前分支是 [$currentBranch]，不是目标分支 [$Branch]。请先切换到 $Branch。"
    }
}

function Ensure-SshRemote() {
    Write-Host ""
    Write-Host "========== 1. 检查 GitHub SSH 连接 ==========" -ForegroundColor Cyan

    $remoteUrl = git remote get-url $Remote 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteUrl)) {
        Fail "未找到远程仓库：$Remote"
    }

    if ($remoteUrl -like "https://github.com/*") {
        $repoPart = $remoteUrl.Replace("https://github.com/", "")
        if ($repoPart.EndsWith(".git")) {
            $repoPart = $repoPart.Substring(0, $repoPart.Length - 4)
        }

        $sshUrl = "git@github.com:$repoPart.git"
        git remote set-url $Remote $sshUrl
        if ($LASTEXITCODE -ne 0) {
            Fail "远程仓库切换 SSH 地址失败。"
        }

        Ok "已将远程仓库从 HTTPS 改为 SSH：$sshUrl"
    }
    elseif ($remoteUrl -like "git@github.com:*" -or $remoteUrl -like "ssh://git@github.com/*") {
        Ok "当前已经使用 SSH 远程仓库：$remoteUrl"
    }
    else {
        Fail "当前远程仓库地址不是 GitHub SSH/HTTPS：$remoteUrl"
    }

    # GitHub SSH 测试成功时通常会输出：
    # Hi username! You've successfully authenticated, but GitHub does not provide shell access.
    # 注意：这条成功提示可能通过 stderr 输出，且 ssh -T 的退出码可能不是 0，所以不能只按退出码判断。
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $sshText = (& ssh -o BatchMode=yes -T git@github.com 2>&1 | Out-String)
    $ErrorActionPreference = $oldErrorActionPreference

    if ($sshText -match "successfully authenticated" -or $sshText -match "Hi\s+.+!.*authenticated") {
        Ok "GitHub SSH 认证正常。"
    }
    else {
        Write-Host $sshText -ForegroundColor Yellow
        Fail "GitHub SSH 认证失败。请先执行 ssh -T git@github.com，并确认 SSH Key 已添加到 GitHub。"
    }
}

function Has-ConflictMarkers() {
    $files = git ls-files
    foreach ($file in $files) {
        if (Test-Path $file) {
            $matched = Select-String -Path $file -Pattern '^\s*(<{7}|={7}|>{7})(\s|$)' -Quiet -ErrorAction SilentlyContinue
            if ($matched) {
                return $true
            }
        }
    }
    return $false
}

function Check-TrackedSecretFiles() {
    $trackedSecrets = @(".env", ".env.local", ".env.prod", ".env.production", ".env.dev", ".env.test")

    foreach ($item in $trackedSecrets) {
        $tracked = git ls-files -- $item
        if ($tracked) {
            Fail "敏感文件已被 Git 跟踪：$item。请先执行：git rm --cached $item"
        }
    }
}

function Test-SensitivePath($path) {
    $p = $path.Replace("\", "/")

    $patterns = @(
        '(^|/)\.env($|\.(local|dev|prod|production|test|staging)$)',
        '(^|/)(id_rsa|id_dsa|id_ecdsa|id_ed25519)$',
        '\.(pem|key|ppk|p12|pfx|jks|kdbx)$',
        '\.(sqlite|sqlite3|db|dump|bak)$',
        '(^|/)(cookies?|tokens?|secrets?|passwords?|credentials?)[^/]*\.(txt|json|yaml|yml|ini|cfg|conf)$'
    )

    foreach ($pattern in $patterns) {
        if ($p -match $pattern) {
            return $true
        }
    }

    return $false
}

function Scan-StagedSecrets() {
    Write-Host ""
    Write-Host "========== 4. 执行隐私与密钥安全扫描 ==========" -ForegroundColor Cyan

    $stagedFiles = git diff --cached --name-only

    if (!$stagedFiles) {
        Ok "没有暂存文件需要扫描。"
        return
    }

    foreach ($file in $stagedFiles) {
        if (Test-SensitivePath $file) {
            Fail "禁止提交疑似敏感文件：$file"
        }
    }

    $secretPatterns = @(
        '-----BEGIN .*PRIVATE KEY-----',
        'gh[pousr]_[A-Za-z0-9_]{20,}',
        'github_pat_[A-Za-z0-9_]{20,}',
        'sk-[A-Za-z0-9_\-]{20,}',
        'xox[baprs]-[A-Za-z0-9\-]{20,}',
        '(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|private[_-]?key|password|passwd|pwd)\s*[:=]\s*["'']?[^"''\s]{8,}',
        '(?i)(postgresql|mysql|mongodb)://[^:\s]+:[^@\s]+@'
    )

    $allowPlaceholders = '(?i)(change_me|your_|example|placeholder|dummy|mock|test|xxxx|xxxxx|<.*>)'

    foreach ($file in $stagedFiles) {
        if (!(Test-Path $file)) {
            continue
        }

        $diffLines = git diff --cached -U0 --no-ext-diff -- $file

        foreach ($line in $diffLines) {
            if (!$line.StartsWith("+")) {
                continue
            }

            if ($line.StartsWith("+++")) {
                continue
            }

            if ($line -match $allowPlaceholders) {
                continue
            }

            foreach ($pattern in $secretPatterns) {
                if ($line -match $pattern) {
                    Write-Host ""
                    Write-Host "文件：$file" -ForegroundColor Yellow
                    Write-Host "疑似敏感新增内容：" -ForegroundColor Yellow
                    Write-Host $line -ForegroundColor Red
                    Fail "检测到疑似密码、Token、密钥或数据库连接串，已阻止提交。"
                }
            }
        }
    }

    Ok "隐私与密钥扫描通过。"
}

function Pull-RemoteSafely() {
    Write-Host ""
    Write-Host "========== 2. 拉取远程更新 ==========" -ForegroundColor Cyan

    git fetch $Remote $Branch
    if ($LASTEXITCODE -ne 0) {
        Fail "git fetch 失败，请检查网络、SSH 权限或 GitHub 状态。"
    }

    $localCommit = (git rev-parse HEAD).Trim()
    $remoteCommit = (git rev-parse "$Remote/$Branch").Trim()
    $baseCommit = (git merge-base HEAD "$Remote/$Branch").Trim()
    $dirty = git status --porcelain

    if ($localCommit -eq $remoteCommit) {
        Ok "本地和远程已经一致。"
        return
    }

    if ($localCommit -eq $baseCommit) {
        if ($dirty) {
            Warn "远程有新提交，同时本地有未提交改动，开始自动 stash。"

            git stash push -u -m "auto backup before sync $(Get-Date -Format 'yyyyMMdd_HHmmss')"
            if ($LASTEXITCODE -ne 0) {
                Fail "自动 stash 失败。"
            }

            git merge --ff-only "$Remote/$Branch"
            if ($LASTEXITCODE -ne 0) {
                Fail "拉取远程更新失败。本地改动已保存在 git stash。"
            }

            git stash pop
            if ($LASTEXITCODE -ne 0) {
                Fail "恢复本地改动时发生冲突。请执行 git status 查看并手动处理。"
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

        return
    }

    if ($remoteCommit -eq $baseCommit) {
        Ok "本地领先远程，准备提交或推送。"
        return
    }

    Fail "本地和远程已经分叉，不能自动同步。请手动检查：git log --oneline --graph --all"
}

function Commit-And-Push() {
    Write-Host ""
    Write-Host "========== 3. 检查本地改动 ==========" -ForegroundColor Cyan

    if (Has-ConflictMarkers) {
        Fail "检测到 Git 冲突标记 <<<<<<< ======= >>>>>>>，请先手动处理。"
    }

    Check-TrackedSecretFiles

    $status = git status --porcelain

    if (!$status) {
        Ok "没有本地改动需要提交。"
    }
    else {
        Write-Host "待处理文件：" -ForegroundColor Cyan
        Write-Host $status

        git add -A
        if ($LASTEXITCODE -ne 0) {
            Fail "git add 失败。"
        }

        Scan-StagedSecrets

        git diff --cached --check
        if ($LASTEXITCODE -ne 0) {
            Fail "git diff --check 发现空白或格式问题。"
        }

        if ([string]::IsNullOrWhiteSpace($Message)) {
            $Message = Read-Host "请输入本次提交说明，例如 feat: add data sync api"
            if ([string]::IsNullOrWhiteSpace($Message)) {
                Fail "提交说明不能为空。"
            }
        }

        git commit -m $Message
        if ($LASTEXITCODE -ne 0) {
            Fail "git commit 失败。"
        }

        Ok "本地改动已提交。"
    }

    if (!$NoPush) {
        Write-Host ""
        Write-Host "========== 5. 推送到 GitHub ==========" -ForegroundColor Cyan

        git push $Remote $Branch
        if ($LASTEXITCODE -ne 0) {
            Fail "git push 失败。可能远程有新提交，请重新运行本脚本。"
        }

        Ok "已推送到 GitHub：$Remote/$Branch"
    }
    else {
        Warn "你指定了 -NoPush，已跳过推送。"
    }
}

function Install-Deps() {
    if ($SkipInstallDeps) {
        Warn "已跳过依赖安装。"
        return
    }

    $venvPython = Join-Path $RepoPath ".venv\Scripts\python.exe"

    if (Test-Path $venvPython) {
        Write-Host ""
        Write-Host "========== 6. 检查 Python 依赖 ==========" -ForegroundColor Cyan

        & $venvPython -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Fail "依赖安装失败。"
        }

        Ok "Python 依赖检查完成。"
    }
    else {
        Warn "未找到 .venv，跳过依赖安装。"
    }
}

try {
    Write-Host "========== koko-qmt SSH 安全同步脚本 ==========" -ForegroundColor Cyan

    Ensure-GitRepo
    Ensure-SshRemote
    Pull-RemoteSafely
    Commit-And-Push
    Install-Deps

    Write-Host ""
    Ok "同步完成：本地和 GitHub 已保持一致。"
}
catch {
    Fail $_.Exception.Message
}

