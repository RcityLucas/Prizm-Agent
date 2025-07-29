# 启动脚本 - 确保SurrealDB服务运行并启动应用

# 检查SurrealDB容器是否已运行
$surrealRunning = docker ps | Select-String -Pattern "surrealdb"

if (-not $surrealRunning) {
    Write-Host "SurrealDB容器未运行，正在启动..."
    # 启动SurrealDB容器
    docker run -d -p 8000:8000 --name rainbow-surrealdb surrealdb/surrealdb:latest start --user root --pass root
    
    # 等待SurrealDB启动
    Write-Host "等待SurrealDB启动..."
    Start-Sleep -Seconds 5
} else {
    Write-Host "SurrealDB容器已运行"
}

# 启动应用
Write-Host "启动RainbowCityAI应用..."
python -m rainbow_agent.app
