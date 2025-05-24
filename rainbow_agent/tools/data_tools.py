"""
数据分析工具

提供数据处理、统计分析和可视化功能
"""
import os
import json
import csv
import base64
from typing import Dict, Any, List, Optional, Union
from io import StringIO
import time

from .base import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入数据分析库，如果不可用则提供基本功能
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas或numpy库未安装，数据分析功能将受限")

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib库未安装，图表生成功能将不可用")


class CSVAnalysisTool(BaseTool):
    """
    CSV数据分析工具
    
    解析和分析CSV格式的数据
    """
    category = "数据分析"
    
    def __init__(self):
        """初始化CSV分析工具"""
        super().__init__(
            name="csv_analysis",
            description="分析CSV格式的数据",
            usage="'[文件路径]' 或 '[命令]|[CSV数据]'"
        )
        
    def run(self, args: str) -> str:
        """
        分析CSV数据
        
        Args:
            args: 文件路径或直接的CSV数据，可选前缀命令:
                  - summary: 生成数据摘要
                  - head: 查看前几行
                  - stats: 生成统计数据
                  - info: 显示数据信息
                  
        Returns:
            分析结果
        """
        if not PANDAS_AVAILABLE:
            return "错误: 此功能需要pandas库支持，请安装pandas和numpy"
            
        try:
            # 解析命令和数据
            command = "summary"  # 默认命令
            if "|" in args:
                command_part, data_part = args.split("|", 1)
                command = command_part.strip().lower()
                data = data_part.strip()
            else:
                data = args.strip()
            
            # 处理数据来源
            df = None
            if os.path.exists(data) and data.endswith(('.csv', '.CSV')):
                # 从文件加载
                logger.info(f"从文件加载CSV数据: {data}")
                df = pd.read_csv(data)
            else:
                # 作为数据字符串处理
                logger.info(f"解析CSV数据字符串")
                df = pd.read_csv(StringIO(data))
            
            # 执行请求的命令
            if command == "head":
                return self._get_head(df)
            elif command == "summary" or command == "info":
                return self._get_summary(df)
            elif command == "stats":
                return self._get_stats(df)
            else:
                return f"未知命令: {command}。支持的命令: summary, head, stats, info"
                
        except Exception as e:
            logger.error(f"CSV分析错误: {e}")
            return f"分析CSV数据时出错: {str(e)}"
    
    def _get_head(self, df: 'pd.DataFrame', n: int = 5) -> str:
        """获取数据前几行"""
        head = df.head(n).to_string()
        return f"数据前{n}行:\n\n{head}"
    
    def _get_summary(self, df: 'pd.DataFrame') -> str:
        """获取数据摘要"""
        buffer = StringIO()
        
        # 基本信息
        buffer.write(f"数据形状: {df.shape[0]}行 x {df.shape[1]}列\n\n")
        
        # 列信息
        buffer.write("列数据类型:\n")
        for col, dtype in df.dtypes.items():
            buffer.write(f"- {col}: {dtype}\n")
            
        # 缺失值信息
        buffer.write("\n缺失值统计:\n")
        for col, missing in df.isnull().sum().items():
            if missing > 0:
                percent = 100 * missing / len(df)
                buffer.write(f"- {col}: {missing} ({percent:.1f}%)\n")
                
        return buffer.getvalue()
    
    def _get_stats(self, df: 'pd.DataFrame') -> str:
        """获取统计数据"""
        try:
            # 只对数值列进行统计
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.empty:
                return "没有找到数值列，无法生成统计数据"
                
            stats = numeric_df.describe().to_string()
            return f"数据统计:\n\n{stats}"
        except Exception as e:
            return f"生成统计数据时出错: {str(e)}"


class DataVisualizationTool(BaseTool):
    """
    数据可视化工具
    
    生成数据可视化图表
    """
    category = "数据分析"
    
    def __init__(self, output_dir: str = "./charts"):
        """
        初始化数据可视化工具
        
        Args:
            output_dir: 图表输出目录
        """
        super().__init__(
            name="data_visualization",
            description="生成数据可视化图表",
            usage="[图表类型]|[数据源]|[选项]"
        )
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def run(self, args: str) -> str:
        """
        创建可视化图表
        
        Args:
            args: 格式为 "图表类型|数据源|选项"
                 - 图表类型: bar, line, scatter, pie, hist
                 - 数据源: CSV文件路径或数据
                 - 选项: JSON格式的可选参数
                 
        Returns:
            创建的图表文件路径或错误信息
        """
        if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
            return "错误: 此功能需要matplotlib和pandas库支持"
            
        try:
            # 解析参数
            parts = args.split("|")
            if len(parts) < 2:
                return "错误: 参数格式应为 '图表类型|数据源|选项'"
                
            chart_type = parts[0].strip().lower()
            data_source = parts[1].strip()
            
            # 解析选项
            options = {}
            if len(parts) > 2:
                try:
                    options = json.loads(parts[2])
                except json.JSONDecodeError:
                    return "错误: 选项应为有效的JSON格式"
            
            # 加载数据
            df = None
            if os.path.exists(data_source) and data_source.endswith(('.csv', '.CSV')):
                # 从文件加载
                logger.info(f"从文件加载数据: {data_source}")
                df = pd.read_csv(data_source)
            else:
                # 作为数据字符串处理
                logger.info("解析CSV数据字符串")
                df = pd.read_csv(StringIO(data_source))
                
            # 创建图表
            timestamp = int(time.time())
            output_file = os.path.join(self.output_dir, f"{chart_type}_{timestamp}.png")
            
            # 设置图表标题
            title = options.get("title", f"{chart_type.capitalize()} Chart")
            
            # 设置图表尺寸
            figsize = options.get("figsize", (8, 6))
            
            # 创建图表
            plt.figure(figsize=figsize)
            
            if chart_type == "bar":
                self._create_bar_chart(df, options, title)
            elif chart_type == "line":
                self._create_line_chart(df, options, title)
            elif chart_type == "scatter":
                self._create_scatter_chart(df, options, title)
            elif chart_type == "pie":
                self._create_pie_chart(df, options, title)
            elif chart_type == "hist":
                self._create_histogram(df, options, title)
            else:
                return f"错误: 不支持的图表类型 '{chart_type}'"
                
            # 保存图表
            plt.tight_layout()
            plt.savefig(output_file, dpi=options.get("dpi", 100))
            plt.close()
            
            return f"图表已保存到: {output_file}"
            
        except Exception as e:
            logger.error(f"创建可视化图表时出错: {e}")
            return f"创建可视化图表时出错: {str(e)}"
    
    def _create_bar_chart(self, df: 'pd.DataFrame', options: Dict[str, Any], title: str):
        """创建条形图"""
        x = options.get("x")
        y = options.get("y")
        
        if x and y and x in df.columns and y in df.columns:
            df.plot(kind='bar', x=x, y=y)
        else:
            # 使用第一列作为X轴，其余数值列作为Y轴
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                df.plot(kind='bar')
            else:
                raise ValueError("数据中没有数值列，无法创建条形图")
                
        plt.title(title)
        plt.xlabel(options.get("xlabel", ""))
        plt.ylabel(options.get("ylabel", ""))
    
    def _create_line_chart(self, df: 'pd.DataFrame', options: Dict[str, Any], title: str):
        """创建折线图"""
        x = options.get("x")
        y = options.get("y")
        
        if x and y and x in df.columns and y in df.columns:
            df.plot(kind='line', x=x, y=y)
        else:
            # 使用索引作为X轴，数值列作为Y轴
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                df.plot(kind='line')
            else:
                raise ValueError("数据中没有数值列，无法创建折线图")
                
        plt.title(title)
        plt.xlabel(options.get("xlabel", ""))
        plt.ylabel(options.get("ylabel", ""))
    
    def _create_scatter_chart(self, df: 'pd.DataFrame', options: Dict[str, Any], title: str):
        """创建散点图"""
        x = options.get("x")
        y = options.get("y")
        
        if not (x and y and x in df.columns and y in df.columns):
            # 尝试使用前两���数值列
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                x, y = numeric_cols[0], numeric_cols[1]
            else:
                raise ValueError("无法确定散点图的X和Y轴，请在选项中明确指定")
                
        plt.scatter(df[x], df[y])
        plt.title(title)
        plt.xlabel(options.get("xlabel", x))
        plt.ylabel(options.get("ylabel", y))
    
    def _create_pie_chart(self, df: 'pd.DataFrame', options: Dict[str, Any], title: str):
        """创建饼图"""
        labels = options.get("labels")
        values = options.get("values")
        
        if labels and values and labels in df.columns and values in df.columns:
            df.plot(kind='pie', y=values, labels=df[labels], autopct='%1.1f%%')
        else:
            # 使用第一列作为标签，第二列作为值
            if df.shape[1] >= 2:
                labels_col = df.columns[0]
                values_col = df.select_dtypes(include=['number']).columns[0] if len(df.select_dtypes(include=['number']).columns) > 0 else df.columns[1]
                df.plot(kind='pie', y=values_col, labels=df[labels_col], autopct='%1.1f%%')
            else:
                raise ValueError("数据不足以创建饼图，需要至少两列")
                
        plt.title(title)
        plt.ylabel("")  # 移除Y轴标签
    
    def _create_histogram(self, df: 'pd.DataFrame', options: Dict[str, Any], title: str):
        """创建直方图"""
        column = options.get("column")
        bins = options.get("bins", 10)
        
        if column and column in df.columns:
            plt.hist(df[column], bins=bins)
        else:
            # 使用第一个数值列
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                plt.hist(df[numeric_cols[0]], bins=bins)
            else:
                raise ValueError("数据中没有数值列，无法创建直方图")
                
        plt.title(title)
        plt.xlabel(options.get("xlabel", column if column else ""))
        plt.ylabel(options.get("ylabel", "频率"))


class JSONProcessingTool(BaseTool):
    """
    JSON处理工具
    
    解析、转换和处理JSON数据
    """
    category = "数据分析"
    
    def __init__(self):
        """初始化JSON处理工具"""
        super().__init__(
            name="json_tool",
            description="处理JSON数据。用法: '命令|JSON数据'。支持的命令: validate, format, extract, convert"
        )
    
    def run(self, args: str) -> str:
        """
        处理JSON数据
        
        Args:
            args: 格式为 "命令|JSON数据"
                 - 命令: validate, format, extract, convert
                 - JSON数据: 要处理的JSON字符串
                 
        Returns:
            处理结果
        """
        try:
            # 解析命令和数据
            if "|" not in args:
                return "错误: 参数格式应为 '命令|JSON数据'"
                
            command, json_data = args.split("|", 1)
            command = command.strip().lower()
            json_data = json_data.strip()
            
            # 执行命令
            if command == "validate":
                return self._validate_json(json_data)
            elif command == "format":
                return self._format_json(json_data)
            elif command == "extract":
                return self._extract_json_keys(json_data)
            elif command == "convert":
                return self._convert_json_to_csv(json_data)
            else:
                return f"错误: 不支持的命令 '{command}'。支持的命令: validate, format, extract, convert"
                
        except Exception as e:
            logger.error(f"JSON处理错误: {e}")
            return f"处理JSON数据时出错: {str(e)}"
    
    def _validate_json(self, json_data: str) -> str:
        """验证JSON数据格式"""
        try:
            data = json.loads(json_data)
            return "有效的JSON格式"
        except json.JSONDecodeError as e:
            return f"无效的JSON格式: {str(e)}"
    
    def _format_json(self, json_data: str) -> str:
        """格式化JSON数据"""
        try:
            data = json.loads(json_data)
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
            return f"格式化的JSON:\n\n{formatted_json}"
        except json.JSONDecodeError as e:
            return f"无效的JSON格式: {str(e)}"
    
    def _extract_json_keys(self, json_data: str) -> str:
        """提取JSON数据中的键"""
        try:
            data = json.loads(json_data)
            
            def extract_keys(obj, prefix=""):
                keys = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        new_key = f"{prefix}.{k}" if prefix else k
                        keys.append(new_key)
                        if isinstance(v, (dict, list)):
                            keys.extend(extract_keys(v, new_key))
                elif isinstance(obj, list) and obj:
                    # 对列表中的第一个元素进行示例提取
                    if obj and isinstance(obj[0], (dict, list)):
                        sample_keys = extract_keys(obj[0], f"{prefix}[0]")
                        keys.extend(sample_keys)
                return keys
            
            all_keys = extract_keys(data)
            return f"JSON键:\n\n" + "\n".join(f"- {key}" for key in all_keys)
            
        except json.JSONDecodeError as e:
            return f"无效的JSON格式: {str(e)}"
    
    def _convert_json_to_csv(self, json_data: str) -> str:
        """将JSON数据转换为CSV格式"""
        try:
            data = json.loads(json_data)
            
            # 只处理列表类型的JSON数据
            if not isinstance(data, list):
                return "错误: 只能转换JSON数组到CSV格式"
                
            if not data:
                return "警告: JSON数组为空"
                
            # 如果数组元素不是字典，尝试转换为简单的CSV
            if not isinstance(data[0], dict):
                csv_output = StringIO()
                writer = csv.writer(csv_output)
                writer.writerow(["Value"])
                for item in data:
                    writer.writerow([item])
                return f"CSV数据:\n\n{csv_output.getvalue()}"
                
            # 提取所有可能的字段名
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            # 转换为CSV
            csv_output = StringIO()
            writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
            return f"CSV数据:\n\n{csv_output.getvalue()}"
            
        except json.JSONDecodeError as e:
            return f"无效的JSON格式: {str(e)}"
