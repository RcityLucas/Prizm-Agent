# Prizm-Agent 服务器部署指南

## 🚀 Docker Compose 部署（推荐）

### 1. 环境准备

```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用用户组更改
```

### 2. 项目配置

```bash
# 克隆项目
git clone <your-repo-url>
cd Prizm-Agent

# 创建环境变量文件
cp .env.example .env
```

**编辑 `.env` 文件**：
```env
# OpenAI API配置
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# SurrealDB配置（Docker内部使用）
SURREALDB_URL=ws://surreal:8000/rpc
SURREALDB_NAMESPACE=rainbow
SURREALDB_DATABASE=production
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=your-strong-password

# 服务器配置
HOST=0.0.0.0
PORT=5000
SECRET_KEY=your-very-secret-key-for-production

# OAuth配置（可选）
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# 前端URL
FRONTEND_BASE_URL=http://your-domain.com
```

### 3. 启动服务

```bash
# 创建数据目录
mkdir -p surreal_data

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 服务访问

- **API服务**: http://your-domain.com:5000
- **SurrealDB**: http://your-domain.com:8001 (管理界面)

## 🔧 生产环境优化

### 1. 更新 docker-compose.yml

```yaml
version: '3.8'

services:
  surreal:
    image: surrealdb/surrealdb:latest
    container_name: prizm_surreal
    command: start --bind 0.0.0.0:8000 --user root --pass ${SURREALDB_PASSWORD} surrealkv:///data/database.db
    ports:
      - "127.0.0.1:8001:8000"  # 仅本地访问
    volumes:
      - ./surreal_data:/data
    restart: always
    networks:
      - prizm_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: prizm_api
    depends_on:
      surreal:
        condition: service_healthy
    ports:
      - "127.0.0.1:5000:5000"  # 仅本地访问
    env_file:
      - ./.env
    environment:
      - SURREALDB_URL=ws://surreal:8000/rpc
      - SURREALDB_NAMESPACE=rainbow
      - SURREALDB_DATABASE=production
      - SURREALDB_USERNAME=root
      - SURREALDB_PASSWORD=${SURREALDB_PASSWORD}
      - HOST=0.0.0.0
      - PORT=5000
    restart: always
    networks:
      - prizm_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/system/status"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./logs:/app/logs

networks:
  prizm_network:
    driver: bridge
```

### 2. Nginx 反向代理配置

**创建 `/etc/nginx/sites-available/prizm-agent`**：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # HTTP重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # SSL优化配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 日志配置
    access_log /var/log/nginx/prizm-agent.access.log;
    error_log /var/log/nginx/prizm-agent.error.log;
    
    # 客户端上传限制
    client_max_body_size 10M;
    
    # 代理到Flask应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API路由优化
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 120s;  # AI响应可能需要更长时间
    }
}
```

**激活配置**：
```bash
sudo ln -s /etc/nginx/sites-available/prizm-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🛠️ 手动部署方式

### 1. 系统准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv curl wget

# CentOS/RHEL
sudo yum install python3 python3-pip curl wget
```

### 2. 安装SurrealDB

```bash
# 下载并安装SurrealDB
curl -sSf https://install.surrealdb.com | sh

# 创建服务文件
sudo tee /etc/systemd/system/surrealdb.service > /dev/null <<EOF
[Unit]
Description=SurrealDB
After=network.target

[Service]
Type=simple
User=surrealdb
Group=surrealdb
WorkingDirectory=/var/lib/surrealdb
ExecStart=/usr/local/bin/surreal start --bind 127.0.0.1:8000 --user root --pass your-password surrealkv:///var/lib/surrealdb/database.db
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 创建用户和目录
sudo useradd -r -s /bin/false surrealdb
sudo mkdir -p /var/lib/surrealdb
sudo chown surrealdb:surrealdb /var/lib/surrealdb

# 启动服务
sudo systemctl enable surrealdb
sudo systemctl start surrealdb
```

### 3. 部署应用

```bash
# 创建应用目录
sudo mkdir -p /opt/prizm-agent
cd /opt/prizm-agent

# 克隆代码
git clone <your-repo-url> .

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --no-cache-dir -r requirements.txt

# 安装langmem包
cd langmem && pip install -e . && cd ..

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库连接等

# 创建服务文件
sudo tee /etc/systemd/system/prizm-agent.service > /dev/null <<EOF
[Unit]
Description=Prizm Agent API Server
After=network.target surrealdb.service
Requires=surrealdb.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/prizm-agent
Environment=PATH=/opt/prizm-agent/venv/bin
ExecStart=/opt/prizm-agent/venv/bin/python surreal_api_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
sudo chown -R www-data:www-data /opt/prizm-agent

# 启动服务
sudo systemctl enable prizm-agent
sudo systemctl start prizm-agent
```

## 📊 监控和维护

### 1. 日志管理

```bash
# 查看应用日志
sudo journalctl -u prizm-agent -f

# 查看SurrealDB日志
sudo journalctl -u surrealdb -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/prizm-agent.access.log
sudo tail -f /var/log/nginx/prizm-agent.error.log
```

### 2. 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

echo "=== Prizm Agent 健康检查 ==="

# 检查服务状态
echo "1. 服务状态检查..."
sudo systemctl is-active surrealdb
sudo systemctl is-active prizm-agent
sudo systemctl is-active nginx

# 检查端口监听
echo "2. 端口监听检查..."
netstat -tlnp | grep :8000  # SurrealDB
netstat -tlnp | grep :5000  # API Server
netstat -tlnp | grep :443   # Nginx HTTPS

# 检查API响应
echo "3. API响应检查..."
curl -s --connect-timeout 5 http://localhost:5000/api/system/status | jq .

echo "健康检查完成"
```

### 3. 备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/prizm-agent"
DATE=$(date +%Y%m%d_%H%M%S)

echo "开始备份 Prizm Agent..."

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份SurrealDB数据
echo "备份数据库..."
cp -R /var/lib/surrealdb $BACKUP_DIR/surrealdb_$DATE

# 备份应用配置
echo "备份应用配置..."
cp /opt/prizm-agent/.env $BACKUP_DIR/env_$DATE

# 压缩旧备份
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;

echo "备份完成: $BACKUP_DIR"
```

## 🔒 安全配置

### 1. 防火墙设置

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 仅允许本地访问SurrealDB和API
sudo ufw deny 8000
sudo ufw deny 5000
```

### 2. SSL证书（Let's Encrypt）

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
```

## 🚀 快速部署命令

```bash
# 一键部署脚本
curl -sSL https://raw.githubusercontent.com/your-repo/Prizm-Agent/main/deploy.sh | bash
```

## ❗ 注意事项

1. **生产环境**请务必：
   - 修改默认密码
   - 配置HTTPS
   - 设置防火墙
   - 定期备份数据

2. **性能优化**：
   - 使用SSD存储
   - 配置适当的内存限制
   - 启用Nginx gzip压缩

3. **监控建议**：
   - 使用Prometheus + Grafana
   - 配置日志收集
   - 设置告警规则

需要具体的部署帮助吗？我可以根据你的服务器环境提供更详细的指导。