#!/bin/bash

# 配置参数
PROJECT_DIR="/data/prizmAi/Prizm-Agent"
PID_FILE="prizm_app.pid"
LOG_FILE="prizm_app.log"
API_BASE="http://127.0.0.1:5000"

cd "$PROJECT_DIR" || {
    echo "❌ 无法切换到项目目录: $PROJECT_DIR"
    exit 1
}

echo "=== Prizm-Agent 健康检查 ==="
echo "时间: $(date)"
echo "项目目录: $PROJECT_DIR"
echo

# 1. 进程检查
echo "1️⃣ 进程状态检查"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "   ✅ 进程运行正常 (PID: $PID)"
        
        # 获取进程信息
        PROCESS_INFO=$(ps -p "$PID" -o pid,ppid,pcpu,pmem,etime,cmd --no-headers)
        echo "   📊 进程信息: $PROCESS_INFO"
        
        # 检查进程启动时间
        START_TIME=$(ps -p "$PID" -o lstart= 2>/dev/null | xargs)
        echo "   🕐 启动时间: $START_TIME"
    else
        echo "   ❌ 进程未运行 (PID: $PID)"
        return 1
    fi
else
    echo "   ❌ PID文件不存在"
    return 1
fi

# 2. 端口检查
echo
echo "2️⃣ 端口监听检查"
if netstat -tlnp 2>/dev/null | grep -q ":5000.*LISTEN"; then
    echo "   ✅ 端口5000监听正常"
    LISTEN_INFO=$(netstat -tlnp 2>/dev/null | grep ":5000.*LISTEN")
    echo "   📡 监听信息: $LISTEN_INFO"
else
    echo "   ❌ 端口5000未监听"
    return 1
fi

# 3. API健康检查
echo
echo "3️⃣ API健康检查"

# 检查系统状态端点
echo "   检查系统状态..."
if RESPONSE=$(curl -s --connect-timeout 5 --max-time 10 "$API_BASE/api/system/status" 2>/dev/null); then
    echo "   ✅ 系统状态API响应正常"
    if echo "$RESPONSE" | grep -q '"success".*true'; then
        echo "   ✅ 系统状态健康"
        # 提取关键信息
        if command -v jq >/dev/null 2>&1; then
            echo "$RESPONSE" | jq -r '   .status | "   📊 存储状态: " + .storage.status + ", 时间: " + .timestamp'
        fi
    else
        echo "   ⚠️ 系统状态异常"
        echo "   响应: $RESPONSE"
    fi
else
    echo "   ❌ 系统状态API无响应"
    return 1
fi

# 检查主页
echo "   检查主页..."
if curl -s --connect-timeout 5 --max-time 10 "$API_BASE/" > /dev/null 2>&1; then
    echo "   ✅ 主页响应正常"
else
    echo "   ⚠️ 主页无响应"
fi

# 检查认证API
echo "   检查认证API..."
if curl -s --connect-timeout 5 --max-time 10 "$API_BASE/api/auth/status" > /dev/null 2>&1; then
    echo "   ✅ 认证API响应正常"
else
    echo "   ⚠️ 认证API无响应"
fi

# 4. 资源使用检查
echo
echo "4️⃣ 资源使用检查"
if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
    # CPU和内存使用
    CPU_MEM=$(ps -p "$PID" -o pcpu,pmem --no-headers)
    echo "   💻 CPU使用: $(echo $CPU_MEM | awk '{print $1}')%"
    echo "   🧠 内存使用: $(echo $CPU_MEM | awk '{print $2}')%"
    
    # 内存详细信息
    if [ -f "/proc/$PID/status" ]; then
        VM_SIZE=$(grep VmSize /proc/$PID/status 2>/dev/null | awk '{print $2 $3}')
        VM_RSS=$(grep VmRSS /proc/$PID/status 2>/dev/null | awk '{print $2 $3}')
        echo "   📏 虚拟内存: $VM_SIZE"
        echo "   📐 物理内存: $VM_RSS"
    fi
    
    # 文件描述符
    if [ -d "/proc/$PID/fd" ]; then
        FD_COUNT=$(ls /proc/$PID/fd 2>/dev/null | wc -l)
        echo "   📂 文件描述符: $FD_COUNT"
    fi
fi

# 5. 磁盘空间检查
echo
echo "5️⃣ 磁盘空间检查"
DISK_USAGE=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
echo "   💾 磁盘使用: ${DISK_USAGE}%"
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "   ⚠️ 磁盘空间不足"
elif [ "$DISK_USAGE" -gt 80 ]; then
    echo "   ⚠️ 磁盘空间紧张"
else
    echo "   ✅ 磁盘空间充足"
fi

# 6. 日志检查
echo
echo "6️⃣ 日志检查"
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
    echo "   📝 日志文件大小: $LOG_SIZE"
    
    # 检查最近的错误
    ERROR_COUNT=$(tail -100 "$LOG_FILE" | grep -i "error\|exception\|failed" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   ⚠️ 最近100行日志中有 $ERROR_COUNT 个错误"
        echo "   最新错误："
        tail -100 "$LOG_FILE" | grep -i "error\|exception\|failed" | tail -3 | sed 's/^/     /'
    else
        echo "   ✅ 最近日志无明显错误"
    fi
    
    # 显示最新日志
    echo "   📋 最新日志 (最后5行):"
    tail -5 "$LOG_FILE" | sed 's/^/     /'
else
    echo "   ⚠️ 日志文件不存在"
fi

# 7. 网络连接检查
echo
echo "7️⃣ 网络连接检查"
if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
    CONNECTIONS=$(netstat -anp 2>/dev/null | grep "$PID" | wc -l)
    echo "   🌐 活跃连接数: $CONNECTIONS"
    
    if [ "$CONNECTIONS" -gt 0 ]; then
        echo "   连接详情:"
        netstat -anp 2>/dev/null | grep "$PID" | head -5 | sed 's/^/     /'
    fi
fi

# 8. 环境检查
echo
echo "8️⃣ 环境检查"
if [ -f ".env" ]; then
    echo "   ✅ 环境配置文件存在"
    ENV_SIZE=$(wc -l < .env)
    echo "   📄 配置项数量: $ENV_SIZE"
else
    echo "   ❌ 环境配置文件缺失"
fi

# Python环境检查
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "   🐍 Conda环境: $CONDA_DEFAULT_ENV"
else
    echo "   🐍 Python版本: $(python --version 2>/dev/null || echo '未找到')"
fi

# 9. 总结
echo
echo "🎯 === 健康检查总结 ==="

# 计算健康分数
HEALTH_SCORE=0
MAX_SCORE=8

# 进程运行 +1
[ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1 && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# 端口监听 +1
netstat -tlnp 2>/dev/null | grep -q ":5000.*LISTEN" && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# API响应 +1
curl -s --connect-timeout 3 "$API_BASE/api/system/status" > /dev/null 2>&1 && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# 磁盘空间 +1
[ "$DISK_USAGE" -lt 80 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# 日志文件存在 +1
[ -f "$LOG_FILE" ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# 错误数量少 +1
[ "$ERROR_COUNT" -lt 5 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# 环境配置 +1
[ -f ".env" ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))

# CPU使用合理 +1
if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
    CPU_USAGE=$(ps -p "$PID" -o pcpu --no-headers | awk '{print int($1)}')
    [ "$CPU_USAGE" -lt 80 ] && HEALTH_SCORE=$((HEALTH_SCORE + 1))
fi

HEALTH_PERCENT=$((HEALTH_SCORE * 100 / MAX_SCORE))

echo "健康评分: $HEALTH_SCORE/$MAX_SCORE ($HEALTH_PERCENT%)"

if [ "$HEALTH_PERCENT" -ge 90 ]; then
    echo "状态: 🟢 优秀"
elif [ "$HEALTH_PERCENT" -ge 70 ]; then
    echo "状态: 🟡 良好"
elif [ "$HEALTH_PERCENT" -ge 50 ]; then
    echo "状态: 🟠 一般"
else
    echo "状态: 🔴 需要关注"
fi

echo
echo "📝 建议操作:"
echo "重启服务: ./restart_prizm_improved.sh"
echo "查看日志: tail -f $LOG_FILE"
echo "查看进程: ps aux | grep surreal_api_server.py"

exit 0