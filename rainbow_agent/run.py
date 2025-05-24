"""
Rainbow Agent 启动脚本

提供便捷的命令行方式启动服务器
"""
import os
import argparse
from rainbow_agent.server import start_server
from rainbow_agent.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description='启动Rainbow Agent服务')
    parser.add_argument('-H', '--host', type=str, default='0.0.0.0',
                        help='服务器主机地址 (默认: 0.0.0.0)')
    parser.add_argument('-p', '--port', type=int, default=8000,
                        help='服务器端口 (默认: 8000)')
    parser.add_argument('-r', '--reload', action='store_true',
                        help='启用热重载 (开发模式)')
    
    args = parser.parse_args()
    
    logger.info(f"启动Rainbow Agent服务: http://{args.host}:{args.port} (热重载: {args.reload})")
    start_server(host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
