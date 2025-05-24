"""
天气查询工具
"""
from typing import Any
from .base import BaseTool
import json
import random

class WeatherTool(BaseTool):
    """天气查询工具，可以查询指定城市的天气情况"""
    
    def __init__(self):
        super().__init__(
            name="WeatherTool",
            description="查询指定城市的天气情况",
            usage="WeatherTool <城市名称>",
            version="1.0.1",
            author="Rainbow Team",
            tags=["天气", "查询", "基础工具"]
        )
        
    def run(self, args: Any) -> str:
        """
        执行天气查询
        
        Args:
            args: 城市名称
            
        Returns:
            天气查询结果
        """
        try:
            city = str(args).strip()
            if not city:
                return "请提供要查询的城市名称"
                
            # 模拟天气API调用
            weather_data = self._simulate_weather_api(city)
            return json.dumps(weather_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"天气查询失败: {str(e)}"
            
    def _simulate_weather_api(self, city: str) -> dict:
        """模拟天气API调用"""
        # 随机生成天气数据
        weather_types = ["晴", "多云", "阴", "小雨", "中雨", "大雨", "雷阵雨", "小雪", "中雪", "大雪"]
        temp_range = {
            "晴": (25, 35),
            "多云": (20, 30),
            "阴": (15, 25),
            "小雨": (15, 20),
            "中雨": (10, 18),
            "大雨": (8, 15),
            "雷阵雨": (12, 22),
            "小雪": (-5, 5),
            "中雪": (-10, 0),
            "大雪": (-15, -5)
        }
        
        weather = random.choice(weather_types)
        temp_min, temp_max = temp_range[weather]
        current_temp = random.randint(temp_min, temp_max)
        
        return {
            "city": city,
            "weather": weather,
            "temperature": current_temp,
            "humidity": random.randint(30, 90),
            "wind": f"{random.randint(0, 10)}级",
            "forecast": [
                {
                    "date": "今天",
                    "weather": weather,
                    "temp_range": f"{current_temp-2}°C ~ {current_temp+2}°C"
                },
                {
                    "date": "明天",
                    "weather": random.choice(weather_types),
                    "temp_range": f"{current_temp-5}°C ~ {current_temp+5}°C"
                },
                {
                    "date": "后天",
                    "weather": random.choice(weather_types),
                    "temp_range": f"{current_temp-8}°C ~ {current_temp+8}°C"
                }
            ]
        }
