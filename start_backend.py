#!/usr/bin/env python3
"""
后端服务启动脚本
确保所有依赖和配置都正确设置
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要3.8+")
        return False
    print(f"✅ Python版本: {sys.version}")
    
    # 检查必要的环境变量
    required_env_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  缺少环境变量: {', '.join(missing_vars)}")
        print("请在.env文件中设置这些变量")
        return False
    
    print("✅ 环境变量配置正确")
    return True

def check_dependencies():
    """检查依赖包"""
    print("📦 检查依赖包...")
    
    required_packages = [
        'flask',
        'flask-cors',
        'flask-login',
        'flask-session',
        'surrealdb',
        'authlib',
        'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def check_surreal_db():
    """检查SurrealDB连接"""
    print("🗄️  检查SurrealDB连接...")
    
    try:
        # 尝试连接SurrealDB
        import requests
        
        # 检查SurrealDB是否在运行
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ SurrealDB运行正常")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print("⚠️  SurrealDB似乎没有运行")
        print("请启动SurrealDB:")
        print("  Windows: start-surreal.ps1")
        print("  Linux/Mac: surreal start --log trace --user root --pass root memory")
        return False
        
    except Exception as e:
        print(f"❌ 检查SurrealDB时出错: {e}")
        return False

def start_server():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['FLASK_DEBUG'] = 'True'
    
    # 确保SECRET_KEY存在
    if not env.get('SECRET_KEY'):
        env['SECRET_KEY'] = 'dev_secret_key_12345'
        print("⚠️  使用临时SECRET_KEY")
    
    # 启动服务器
    try:
        cmd = [sys.executable, 'surreal_api_server.py']
        print(f"执行命令: {' '.join(cmd)}")
        
        # 使用subprocess启动服务器
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print("✅ 后端服务已启动")
        print("📍 服务地址: http://localhost:5000")
        print("📍 API文档: http://localhost:5000/api/auth/status")
        print("\n📝 实时日志:")
        print("-" * 50)
        
        # 实时显示日志
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
            
    except KeyboardInterrupt:
        print("\n\n🛑 收到中断信号，正在停止服务器...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🌈 Rainbow Agent 后端服务启动器")
    print("=" * 60)
    
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"📂 工作目录: {project_root}")
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 已加载.env文件")
    except ImportError:
        print("⚠️  python-dotenv未安装，跳过.env文件加载")
    except Exception as e:
        print(f"⚠️  加载.env文件失败: {e}")
    
    # 执行检查
    checks = [
        check_environment,
        check_dependencies,
        check_surreal_db
    ]
    
    for check in checks:
        if not check():
            print(f"\n❌ 检查失败: {check.__name__}")
            print("请修复上述问题后重试")
            return False
        print()
    
    print("🎉 所有检查通过，开始启动服务器...")
    print()
    
    # 启动服务器
    start_server()

if __name__ == '__main__':
    main()