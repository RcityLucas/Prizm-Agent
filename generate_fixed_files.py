#!/usr/bin/env python3
"""
生成修复后的代码文件
用于手动上传到服务器
"""

import os
import shutil
from pathlib import Path

def generate_fixed_files():
    """生成修复后的文件"""
    print("🔧 生成修复后的代码文件...")
    
    # 创建输出目录
    output_dir = Path("fixed_files_for_upload")
    output_dir.mkdir(exist_ok=True)
    
    # 复制修复后的文件
    files_to_copy = [
        "rainbow_agent/auth/routes.py",
        "BUG_FIX_SUMMARY.md",
        "test_variable_fix.py"
    ]
    
    for file_path in files_to_copy:
        src = Path(file_path)
        if src.exists():
            # 保持目录结构
            dst = output_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"✅ 复制: {file_path} -> {dst}")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    # 生成部署说明
    deploy_instructions = """# 部署说明

## 修复的问题
- 修复了注册功能中的变量名不匹配错误
- 解决了 'NoneType' object has no attribute 'create_user_sync' 错误

## 部署步骤

1. 将 `rainbow_agent/auth/routes.py` 上传到服务器对应位置
2. 重启服务：
   ```bash
   # 停止服务
   pkill -f "python.*app.py\\|python.*surreal_api_server.py"
   
   # 启动服务
   cd /data/prizmAi/Prizm-Agent
   python surreal_api_server.py
   ```

3. 测试修复效果：
   ```bash
   python test_variable_fix.py
   ```

## 修复内容
- 统一使用 user_storage 变量名
- 修复了3处变量名不一致的问题
- 保持了代码逻辑完全不变

## 预期结果
- 注册功能恢复正常
- 不再出现 'NoneType' 错误
- 用户可以正常注册和登录
"""
    
    with open(output_dir / "DEPLOY_INSTRUCTIONS.md", "w", encoding="utf-8") as f:
        f.write(deploy_instructions)
    
    print(f"\n📦 文件已生成到目录: {output_dir}")
    print("📋 包含文件:")
    for file in output_dir.rglob("*"):
        if file.is_file():
            print(f"  - {file.relative_to(output_dir)}")
    
    print(f"\n🚀 下一步:")
    print(f"1. 将 {output_dir} 目录中的文件上传到服务器")
    print(f"2. 按照 DEPLOY_INSTRUCTIONS.md 中的说明部署")
    print(f"3. 运行测试脚本验证修复效果")

if __name__ == "__main__":
    generate_fixed_files()