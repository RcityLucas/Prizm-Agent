# 如何启用彩虹城AI特色功能

## 快速启用

### 方法一：通过代码配置

```python
from rainbow_agent.config.ai_settings import AISettings
from rainbow_agent.core.dialogue_manager import DialogueManager

# 创建AI设置实例
ai_settings = AISettings()

# 启用彩虹城个性
ai_settings.settings["behavior"]["personality"] = "rainbow_city"

# 创建对话管理器
dialogue_manager = DialogueManager(ai_settings=ai_settings)

# 现在AI会使用彩虹城特色回复！
```

### 方法二：通过配置文件

1. 在项目的`data/settings/`目录下创建或编辑用户设置文件（例如`default_ai_settings.json`）

2. 添加以下配置：

```json
{
  "behavior": {
    "personality": "rainbow_city",
    "response_style": "colorful",
    "rainbow_traits": {
      "use_rainbow_metaphors": true,
      "seasonal_awareness": true,
      "emotional_coloring": true,
      "wisdom_sharing": true,
      "encouraging_tone": true
    },
    "character_traits": {
      "warmth": 9,
      "playfulness": 7,
      "optimism": 9,
      "wisdom": 8
    }
  }
}
```

### 方法三：环境变量

设置环境变量来启用彩虹城模式：

```bash
export AI_PERSONALITY=rainbow_city
export AI_RESPONSE_STYLE=colorful
```

## 验证启用状态

运行以下代码检查是否成功启用：

```python
from rainbow_agent.config.ai_settings import AISettings

settings = AISettings()
personality = settings.get_setting("behavior", "personality")

if personality == "rainbow_city":
    print("🌈 彩虹城AI已启用！")
else:
    print(f"当前个性: {personality}")
```

## 自定义配置

### 调整个性特征

```python
# 修改个性特征强度（1-10分）
ai_settings.settings["behavior"]["character_traits"] = {
    "curiosity": 8,      # 好奇心
    "warmth": 9,         # 温暖度
    "playfulness": 7,    # 玩心
    "wisdom": 8,         # 智慧感
    "optimism": 9,       # 乐观程度
    "patience": 9,       # 耐心程度
    "authenticity": 8,   # 真实感
    "adaptability": 8,   # 适应性
}
```

### 启用/禁用特色功能

```python
# 自定义彩虹城特色功能
ai_settings.settings["behavior"]["rainbow_traits"] = {
    "use_rainbow_metaphors": True,      # 使用彩虹比喻
    "seasonal_awareness": True,         # 季节感知
    "emotional_coloring": True,         # 情感色彩
    "wisdom_sharing": True,             # 智慧分享
    "cultural_blend": True,             # 多元文化
    "poetic_touch": True,               # 诗意表达
    "encouraging_tone": True,           # 鼓励语调
    "memory_weaving": True,             # 记忆编织
}
```

## 效果对比

### 传统模式 (helpful)
```
用户: 我今天心情不好
AI: 我理解你的感受。有什么特别的原因吗？我可以帮你分析一下情况。
```

### 彩虹城模式 (rainbow_city)
```
用户: 我今天心情不好
AI: 我能感受到你心中的蓝色情绪，就像雨天的天空一样。不过请记住，彩虹总是在风雨之后出现的～每一种情感都像色彩一样有它的意义，让我陪伴你一起度过这段时光。✨
```

## 注意事项

1. **向后兼容性**: 新功能默认关闭，不会影响现有用户
2. **性能影响**: 彩虹城模式会略微增加响应生成时间
3. **个性化程度**: 可以通过调整特征数值控制"彩虹"程度
4. **语言支持**: 目前主要针对中文优化，其他语言支持有限

## 故障排除

### 功能未生效
```python
# 检查个性设置
print(ai_settings.get_setting("behavior", "personality"))

# 检查增强器状态
from rainbow_agent.core.response_enhancer import ResponseEnhancer
enhancer = ResponseEnhancer(ai_settings)
print("增强器已初始化" if enhancer else "增强器初始化失败")
```

### 回复过于"彩虹"
```python
# 降低个性特征强度
ai_settings.settings["behavior"]["character_traits"]["playfulness"] = 5
ai_settings.settings["behavior"]["character_traits"]["warmth"] = 7
```

### 回复不够"彩虹"
```python
# 提高个性特征强度
ai_settings.settings["behavior"]["character_traits"]["playfulness"] = 9
ai_settings.settings["behavior"]["character_traits"]["warmth"] = 10
```

## 技术支持

如果遇到问题，请检查：
1. AI设置是否正确保存
2. 对话管理器是否使用了正确的ai_settings参数
3. 日志中是否有相关错误信息