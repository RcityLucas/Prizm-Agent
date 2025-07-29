#!/bin/bash
# 自动检测项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "项目目录: $SCRIPT_DIR"

echo "=== Prizm-Agent 重启脚本 (修复环境) ==="
echo "时间: $(date)"

# 1. 停止服务
echo "1. 停止当前服务..."
pkill -f "surreal_api_server.py" 2>/dev/null
rm -f prizm_app.pid
echo "   服务已停止"

# 2. 更新代码
echo "2. 更新代码..."
cp .env .env.backup 2>/dev/null
git fetch origin
git pull origin main
cp .env.backup .env 2>/dev/null
echo "   代码已更新"

# 3. 初始化 conda（关键步骤）
echo "3. 初始化 conda 环境..."
export PATH="/opt/miniconda3/bin:$PATH"

# 初始化 conda for bash
eval "$(/opt/miniconda3/bin/conda shell.bash hook)"

# 激活 prizm 环境
conda activate prizm

# 验证环境
echo "   当前环境: $CONDA_DEFAULT_ENV"
echo "   Python路径: $(which python)"

# 4. 检查依赖
echo "4. 检查并安装依赖..."
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ flask-login flask-session flask-cors --quiet

# 验证关键依赖
python -c "
try:
    from flask_login import current_user, login_required
    from flask_session import Session
    print('   ✓ 依赖检查通过')
except ImportError as e:
    print(f'   ✗ 依赖缺失: {e}')
    exit(1)
" || exit 1

# 5. 启动服务
echo "5. 启动新服务..."
rm -f prizm_app.log
nohup python surreal_api_server.py > prizm_app.log 2>&1 &
echo $! > prizm_app.pid

# 6. 等待启动
echo "6. 等待服务启动..."
sleep 15

# 7. 验证服务
echo "7. 验证服务状态..."
PID=$(cat prizm_app.pid)
if ps -p $PID > /dev/null 2>&1; then
    echo "   ✓ 进程运行正常 (PID: $PID)"
else
    echo "   ✗ 进程启动失败，查看日志:"
    tail -10 prizm_app.log
    exit 1
fi

# 测试服务响应
sleep 5
if curl -s --connect-timeout 10 http://127.0.0.1:5000/api/system/status > /dev/null; then
    echo "   ✓ 服务响应正常"
    echo "=== 重启成功 ==="
else
    echo "   ⚠ 服务启动但可能还在初始化，查看日志:"
    tail -5 prizm_app.log
fi

echo ""
echo "管理命令:"
echo "查看日志: tail -f prizm_app.log"
echo "检查进程: ps aux | grep surreal_api_server.py"
echo "测试服务: curl http://127.0.0.1:5000/api/system/status"
echo "测试认证: curl http://127.0.0.1:5000/api/auth/status"
