#!/bin/bash

echo "🔍 检查 Docker 启动的 SurrealDB 数据库状态"
echo "=" * 60

# 1. 检查所有运行的容器
echo "1️⃣ 检查运行中的 Docker 容器..."
docker ps

echo -e "\n"

# 2. 检查所有容器（包括停止的）
echo "2️⃣ 检查所有 Docker 容器（包括停止的）..."
docker ps -a

echo -e "\n"

# 3. 查找 SurrealDB 相关容器
echo "3️⃣ 查找 SurrealDB 相关容器..."
docker ps -a | grep -i surreal || echo "未找到 SurrealDB 容器"

echo -e "\n"

# 4. 检查网络端口占用
echo "4️⃣ 检查端口 8000 占用情况..."
netstat -tlnp | grep :8000 || echo "端口 8000 未被占用"

echo -e "\n"

# 5. 检查是否有 docker-compose
echo "5️⃣ 检查 docker-compose 配置..."
if [ -f "docker-compose.yml" ]; then
    echo "找到 docker-compose.yml 文件"
    echo "Docker Compose 服务状态:"
    docker-compose ps 2>/dev/null || echo "Docker Compose 未运行或配置有误"
else
    echo "未找到 docker-compose.yml 文件"
fi

echo -e "\n"

# 6. 测试数据库连接
echo "6️⃣ 测试数据库连接..."
curl -s -X POST \
  -H "Accept: application/json" \
  -H "NS: rainbow" \
  -H "DB: test" \
  -u "root:root" \
  -d "INFO FOR DB;" \
  http://127.0.0.1:8000/sql || echo "数据库连接失败"

echo -e "\n"

echo "📋 检查完成！"
echo "如果需要启动 SurrealDB 容器，请使用以下命令之一："
echo "方法1 - 直接启动: docker run -d --name surrealdb -p 8000:8000 surrealdb/surrealdb:latest start --user root --pass root file:///data/database.db"
echo "方法2 - 使用 docker-compose: docker-compose up -d"
echo "方法3 - 重启现有容器: docker start <容器名或ID>"