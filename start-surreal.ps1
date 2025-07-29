# 设置路径变量
$SurrealDBPath = "D:/SurrealDB/SurrealDBsurreal.exe"
$DatabasePath = "E:/github/Prizm-Agent/rainbow_agent/db-new"
$Port = 8000

# 显示标题
Write-Host "`n🚀 正在准备启动 SurrealDB..." -ForegroundColor Cyan

# 检查 SurrealDB 可执行文件是否存在
if (!(Test-Path $SurrealDBPath)) {
    Write-Host "❌ 错误：未找到 SurrealDB 可执行文件：$SurrealDBPath" -ForegroundColor Red
    pause
    exit 1
}

# 添加端口转发（避免重复添加）
Write-Host "🔧 检查并添加端口转发规则（0.0.0.0:$Port → 127.0.0.1:$Port）..."
$existing = netsh interface portproxy show all | Select-String "0.0.0.0\s+$Port"
if ($existing) {
    Write-Host "✅ 已存在端口转发规则，跳过添加。"
} else {
    netsh interface portproxy add v4tov4 listenport=$Port listenaddress=0.0.0.0 connectport=$Port connectaddress=127.0.0.1
    Write-Host "✅ 添加端口转发规则成功。"
}

# 启动 SurrealDB
Write-Host "`n🚀 正在启动 SurrealDB 数据库服务..." -ForegroundColor Green
& $SurrealDBPath start --bind 0.0.0.0:$Port --user root --pass root "surrealkv://$DatabasePath"

# 防止闪退（仅当主进程非阻塞时有效）
Write-Host "`n✨ 启动命令已执行完毕。按任意键退出窗口..." -ForegroundColor Yellow
[void][System.Console]::ReadKey($true)
