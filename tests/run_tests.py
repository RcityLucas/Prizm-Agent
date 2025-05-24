#!/usr/bin/env python
"""
Rainbow Agent 测试套件执行器

执行所有测试用例并生成测试报告
"""
import unittest
import sys
import os
import time

# 确保可以引入rainbow_agent模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rainbow_agent.utils.logger import setup_logger, get_logger

# 设置日志记录器
setup_logger()
logger = get_logger(__name__)


def run_test_suite():
    """运行完整测试套件"""
    start_time = time.time()
    
    # 自动发现并加载所有测试用例
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # 配置测试结果输出
    verbosity = 2  # 详细输出
    
    # 创建测试结果目录
    results_dir = os.path.join(start_dir, "../test_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # 选择是否输出到文件
    output_to_file = len(sys.argv) > 1 and sys.argv[1] == "--file"
    
    if output_to_file:
        # 输出到文件
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(results_dir, f"test_results_{timestamp}.txt")
        with open(result_file, 'w') as f:
            runner = unittest.TextTestRunner(stream=f, verbosity=verbosity)
            result = runner.run(suite)
        print(f"测试结果已保存到: {result_file}")
    else:
        # 输出到控制台
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
    
    # 计算并显示执行时间
    elapsed_time = time.time() - start_time
    
    # 显示摘要
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    success = total - failures - errors - skipped
    
    summary = f"""
测试执行摘要:
=============
总测试数: {total}
通过: {success}
失败: {failures}
错误: {errors}
跳过: {skipped}
执行时间: {elapsed_time:.2f} 秒
"""
    print(summary)
    
    if output_to_file:
        with open(result_file, 'a') as f:
            f.write(summary)
    
    # 返回退出代码，如果有错误或失败则返回非零值
    return 0 if failures == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(run_test_suite())
