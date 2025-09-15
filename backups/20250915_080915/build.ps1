# SuperAI 自动化构建脚本
# 优化的依赖管理和Docker构建流程

param(
    [string]$Target = "all",
    [switch]$Clean = $false,
    [switch]$NoCache = $false
)

Write-Host "=== SuperAI 构建脚本 ===" -ForegroundColor Green
Write-Host "目标: $Target" -ForegroundColor Yellow

# 清理选项
if ($Clean) {
    Write-Host "清理旧镜像..." -ForegroundColor Yellow
    docker image prune -f
    docker rmi superai-base:latest -f 2>$null
    docker rmi superai-agent-planner:latest -f 2>$null
    docker rmi superai-agent-executor:latest -f 2>$null
}

# 构建参数
$BuildArgs = @()
if ($NoCache) {
    $BuildArgs += "--no-cache"
}

try {
    switch ($Target) {
        "base" {
            Write-Host "构建基础镜像..." -ForegroundColor Cyan
            docker build -t superai-base:latest -f Dockerfile.base . @BuildArgs
        }
        "planner" {
            Write-Host "构建Agent-Planner..." -ForegroundColor Cyan
            docker build -t superai-agent-planner:latest -f microservices/agent-planner/Dockerfile.agi . @BuildArgs
        }
        "executor" {
            Write-Host "构建Agent-Executor..." -ForegroundColor Cyan
            docker build -t superai-agent-executor:latest -f microservices/agent-executor/Dockerfile.agi . @BuildArgs
        }
        "all" {
            Write-Host "构建所有镜像..." -ForegroundColor Cyan
            
            # 1. 构建基础镜像
            Write-Host "[1/3] 构建基础镜像..." -ForegroundColor Blue
            docker build -t superai-base:latest -f Dockerfile.base . @BuildArgs
            if ($LASTEXITCODE -ne 0) { throw "基础镜像构建失败" }
            
            # 2. 构建Agent-Planner
            Write-Host "[2/3] 构建Agent-Planner..." -ForegroundColor Blue
            docker build -t superai-agent-planner:latest -f microservices/agent-planner/Dockerfile.agi . @BuildArgs
            if ($LASTEXITCODE -ne 0) { throw "Agent-Planner构建失败" }
            
            # 3. 构建Agent-Executor
            Write-Host "[3/3] 构建Agent-Executor..." -ForegroundColor Blue
            docker build -t superai-agent-executor:latest -f microservices/agent-executor/Dockerfile.agi . @BuildArgs
            if ($LASTEXITCODE -ne 0) { throw "Agent-Executor构建失败" }
        }
        default {
            Write-Host "未知目标: $Target" -ForegroundColor Red
            Write-Host "可用目标: base, planner, executor, all" -ForegroundColor Yellow
            exit 1
        }
    }
    
    Write-Host "✅ 构建完成!" -ForegroundColor Green
    
    # 显示镜像信息
    Write-Host "\n=== 构建的镜像 ===" -ForegroundColor Green
    docker images | Select-String "superai"
    
} catch {
    Write-Host "❌ 构建失败: $_" -ForegroundColor Red
    exit 1
}

# 使用示例：
# .\build.ps1                    # 构建所有镜像
# .\build.ps1 -Target base       # 只构建基础镜像
# .\build.ps1 -Clean             # 清理后构建
# .\build.ps1 -NoCache           # 无缓存构建