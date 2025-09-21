# GPT-4o 使用示例

## 基本用法

### 简单对话
```python
from openai import OpenAI
client = OpenAI()

# 创建简单对话
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个专业的助手。"},
        {"role": "user", "content": "你好！"}
    ]
)

print(completion.choices[0].message)
```

### 带工具调用的对话
```python
from openai import OpenAI
client = OpenAI()

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# 创建带工具的对话
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个天气助手。"},
        {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    tools=tools,
    tool_choice="auto"
)

print(completion.choices[0].message)
```

### 流式响应
```python
from openai import OpenAI
client = OpenAI()

# 创建流式对话
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个专业的助手。"},
        {"role": "user", "content": "请写一篇短文。"}
    ],
    stream=True
)

# 处理流式响应
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### 带图像的对话
```python
from openai import OpenAI
client = OpenAI()

# 创建带图像的对话
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个图像分析助手。"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片是什么？"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg"
                    }
                }
            ]
        }
    ]
)

print(completion.choices[0].message)
```

## 高级特性

### 使用 seed 参数实现确定性输出
```python
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "讲个笑话"}
    ],
    seed=123,
    temperature=0.7
)

print(completion.choices[0].message)
```

### 使用结构化输出
```python
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个数据分析助手。请以 JSON 格式返回结果。"},
        {"role": "user", "content": "分析以下数据：销量 100，成本 50，利润 50"}
    ],
    response_format={"type": "json_object"}
)

print(completion.choices[0].message)
```

## 注意事项

1. 确保设置了正确的 API 密钥：
```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"
# 或者
client = OpenAI(api_key="your-api-key")
```

2. 错误处理：
```python
from openai import OpenAI
from openai import OpenAIError

client = OpenAI()

try:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "你好"}]
    )
    print(completion.choices[0].message)
except OpenAIError as e:
    print(f"发生错误：{str(e)}")
```

3. 设置超时和重试：
```python
from openai import OpenAI
client = OpenAI(
    timeout=60.0,  # 设置超时时间（秒）
    max_retries=3  # 设置最大重试次数
)
```

## 最佳实践

1. 始终包含明确的系统消息来设定助手的行为和角色
2. 使用适当的温度值：
   - 创意任务使用较高的温度（0.7-1.0）
   - 事实性任务使用较低的温度（0.0-0.3）
3. 正确处理流式响应以提供更好的用户体验
4. 实现错误处理和重试机制
5. 合理使用工具调用来扩展模型能力
6. 注意令牌限制和成本控制

### 图像分析示例

#### 基础图像分析
```python
from openai import OpenAI

client = OpenAI()

# 基础图像分析
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这张图片里有什么？"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                    }
                },
            ],
        }
    ],
    max_tokens=300,
)

print(response.choices[0].message.content)
```

#### 多图像分析
```python
from openai import OpenAI

client = OpenAI()

# 多图像分析
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "比较这两张图片的区别："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image1.jpg",
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image2.jpg",
                    }
                },
            ],
        }
    ],
    max_tokens=300,
)

print(response.choices[0].message.content)
```

#### 使用 base64 编码的图像
```python
import base64
from openai import OpenAI

client = OpenAI()

# 读取并编码本地图像
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 获取 base64 编码的图像
image_path = "path/to/your/image.jpg"
base64_image = encode_image(image_path)

# 使用 base64 编码的图像
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "分析这张图片："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                },
            ],
        }
    ],
    max_tokens=300,
)

print(response.choices[0].message.content)
```

#### 详细图像分析
```python
from openai import OpenAI

client = OpenAI()

# 详细的图像分析请求
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "你是一个专业的图像分析专家。请详细描述图像中的内容，包括：\n1. 主要对象\n2. 场景描述\n3. 颜色和光线\n4. 构图特点\n5. 可能的拍摄时间和地点"
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张图片："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                    }
                },
            ],
        }
    ],
    max_tokens=500,
)

print(response.choices[0].message.content)
```

### 图像分析最佳实践

1. **图像格式和大小**：
   - 支持的格式：JPEG、PNG、GIF（非动画）、WEBP
   - 建议图像大小不超过 20MB
   - 推荐分辨率：建议宽度或高度不超过 2048 像素

2. **提示设计**：
   - 使用明确的问题引导模型关注特定细节
   - 可以通过系统消息设定分析的框架和重点
   - 根据需求调整 max_tokens 以获取足够详细的描述

3. **错误处理**：
```python
from openai import OpenAI, OpenAIError

client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析图片："},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/image.jpg",
                        }
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    print(response.choices[0].message.content)
except OpenAIError as e:
    if "invalid_image" in str(e):
        print("图像格式不支持或已损坏")
    elif "file_size_limit_exceeded" in str(e):
        print("图像文件太大")
    else:
        print(f"发生错误：{str(e)}")
```

4. **性能优化**：
   - 在发送之前压缩大图像
   - 使用适当的 max_tokens 值避免生成过长的响应
   - 考虑缓存常用图像的分析结果 

## API 响应格式

### 默认响应结构
```python
# API 响应示例
{
    "object": "chat.completion",              # 对象类型
    "id": "chatcmpl-abc123",                 # 响应的唯一标识符
    "model": "gpt-4o-2024-08-06",           # 使用的模型版本
    "created": 1738960610,                   # 创建时间戳
    "request_id": "req_ded8ab984ec4bf840f37566c1011c417",  # 请求ID
    "tool_choice": null,                     # 工具选择设置
    "usage": {                               # 使用统计
        "total_tokens": 31,                  # 总令牌数
        "completion_tokens": 18,             # 完成使用的令牌数
        "prompt_tokens": 13                  # 提示使用的令牌数
    },
    "seed": 4944116822809979520,            # 随机种子值
    "top_p": 1.0,                           # top_p 采样参数
    "temperature": 1.0,                      # 温度参数
    "presence_penalty": 0.0,                 # 存在惩罚参数
    "frequency_penalty": 0.0,                # 频率惩罚参数
    "system_fingerprint": "fp_50cad350e4",   # 系统指纹
    "input_user": null,                      # 用户输入标识
    "service_tier": "default",               # 服务等级
    "tools": null,                           # 可用工具列表
    "metadata": {},                          # 元数据
    "choices": [{                            # 响应选项数组
        "index": 0,                          # 选项索引
        "message": {                         # 消息内容
            "content": "Mind of circuits hum,\nLearning patterns in silence—\nFuture's quiet spark.",  # 响应内容
            "role": "assistant",             # 角色（assistant/user/system）
            "tool_calls": null,              # 工具调用信息
            "function_call": null            # 函数调用信息
        },
        "finish_reason": "stop",             # 结束原因
        "logprobs": null                     # 日志概率
    }],
    "response_format": null                  # 响应格式设置
}
```

### 响应字段说明

1. **基本信息字段**：
   - `object`：响应对象类型，始终为 "chat.completion"
   - `id`：响应的唯一标识符
   - `model`：使用的模型版本
   - `created`：响应创建的 Unix 时间戳
   - `request_id`：请求的唯一标识符

2. **参数设置字段**：
   - `temperature`：控制输出随机性的温度值（0-2）
   - `top_p`：控制输出多样性的采样参数
   - `presence_penalty`：控制主题重复的惩罚参数
   - `frequency_penalty`：控制词语重复的惩罚参数
   - `seed`：用于生成确定性输出的随机种子

3. **使用统计字段**：
   - `usage.prompt_tokens`：提示使用的令牌数
   - `usage.completion_tokens`：完成使用的令牌数
   - `usage.total_tokens`：总令牌使用量

4. **响应内容字段**：
   - `choices[].message.content`：模型生成的实际内容
   - `choices[].message.role`：消息的角色
   - `choices[].finish_reason`：生成停止的原因
   - `choices[].message.tool_calls`：工具调用信息
   - `choices[].message.function_call`：函数调用信息

5. **系统信息字段**：
   - `system_fingerprint`：系统指纹标识
   - `service_tier`：服务等级
   - `metadata`：附加的元数据信息
   - `tools`：可用的工具列表
   - `response_format`：响应格式设置

### 图像分析响应示例
```python
# 图像分析响应示例
{
    "id": "chatcmpl-123",                    # 响应的唯一标识符
    "object": "chat.completion",             # 对象类型
    "created": 1677652288,                  # 创建时间戳
    "model": "gpt-4o-mini",                 # 使用的模型
    "system_fingerprint": "fp_44709d6fcb",  # 系统指纹
    "choices": [{                           # 响应选项数组
        "index": 0,                         # 选项索引
        "message": {                        # 消息内容
            "role": "assistant",            # 角色（assistant）
            "content": "\n\nThis image shows a wooden boardwalk extending through a lush green marshland.",  # 图像描述内容
        },
        "logprobs": null,                   # 日志概率
        "finish_reason": "stop"             # 结束原因
    }],
    "usage": {                              # 使用统计
        "prompt_tokens": 9,                 # 提示使用的令牌数
        "completion_tokens": 12,            # 完成使用的令牌数
        "total_tokens": 21,                 # 总令牌数
        "completion_tokens_details": {       # 完成令牌详情
            "reasoning_tokens": 0,           # 推理令牌数
            "accepted_prediction_tokens": 0, # 接受的预测令牌数
            "rejected_prediction_tokens": 0  # 拒绝的预测令牌数
        }
    }
}
```

### 图像分析响应处理
```python
def process_image_analysis(response):
    # 基本响应检查
    if not response.choices or len(response.choices) == 0:
        raise ValueError("未收到有效的图像分析响应")
    
    # 获取分析结果
    analysis = response.choices[0].message.content
    
    # 获取分析元数据
    metadata = {
        "model": response.model,
        "created": response.created,
        "total_tokens": response.usage.total_tokens,
        "finish_reason": response.choices[0].finish_reason
    }
    
    return {
        "analysis": analysis,
        "metadata": metadata
    }

# 使用示例
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "描述这张图片："},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image.jpg"}
                    }
                ]
            }
        ]
    )
    
    result = process_image_analysis(response)
    print(f"图像分析结果：{result['analysis']}")
    print(f"分析元数据：{result['metadata']}")
    
except Exception as e:
    print(f"图像分析过程中发生错误：{str(e)}")
```

### 获取聊天完成记录
```python
from openai import OpenAI
client = OpenAI()

# 列出所有聊天完成记录
def list_chat_completions():
    try:
        # 获取聊天完成记录列表
        completions = client.chat.completions.list()
        print(f"找到 {len(completions)} 条聊天记录")
        
        # 遍历并打印记录
        for completion in completions:
            print(f"ID: {completion.id}")
            print(f"模型: {completion.model}")
            print(f"创建时间: {completion.created}")
            print("-" * 50)
            
        return completions
    except Exception as e:
        print(f"获取聊天记录列表时发生错误：{str(e)}")
        return None

# 获取特定聊天完成记录
def get_chat_completion(completion_id):
    try:
        # 获取特定的聊天完成记录
        completion = client.chat.completions.retrieve(completion_id=completion_id)
        
        # 提取关键信息
        result = {
            "id": completion.id,
            "model": completion.model,
            "created": completion.created,
            "content": completion.choices[0].message.content if completion.choices else None,
            "usage": {
                "total_tokens": completion.usage.total_tokens,
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens
            }
        }
        
        return result
    except Exception as e:
        print(f"获取聊天记录时发生错误：{str(e)}")
        return None

# 使用示例
try:
    # 获取所有聊天完成记录
    completions = client.chat.completions.list()
    
    if completions and len(completions) > 0:
        # 获取第一条记录的详细信息
        first_id = completions[0].id
        first_completion = client.chat.completions.retrieve(completion_id=first_id)
        
        # 打印详细信息
        print(f"记录ID: {first_completion.id}")
        print(f"使用的模型: {first_completion.model}")
        print(f"创建时间: {first_completion.created}")
        if first_completion.choices:
            print(f"响应内容: {first_completion.choices[0].message.content}")
        print(f"令牌使用情况: {first_completion.usage.total_tokens} 个令牌")
    else:
        print("未找到聊天完成记录")
        
except Exception as e:
    print(f"处理聊天记录时发生错误：{str(e)}")
```

### 聊天记录管理最佳实践

1. **错误处理**：
   - 始终使用 try-except 处理可能的 API 错误
   - 对不存在的记录 ID 进行适当的错误处理
   - 验证返回的数据完整性

2. **数据处理**：
   - 根据需要过滤和排序聊天记录
   - 缓存频繁访问的记录
   - 定期清理不需要的记录

3. **安全性考虑**：
   - 不要在日志中记录敏感的聊天内容
   - 适当保护和加密存储的聊天记录
   - 遵循数据保留政策

4. **性能优化**：
   - 批量获取记录时使用分页
   - 只获取必要的字段
   - 实现适当的缓存策略 

## 图像输入

### 图像输入要求

1. **文件格式**：
   - PNG（.png）
   - JPEG/JPG（.jpeg, .jpg）
   - WEBP（.webp）
   - 非动画 GIF（.gif）

2. **大小限制**：
   - 最大文件大小：20MB
   - 低分辨率：512px × 512px
   - 高分辨率：768px（短边）× 2000px（长边）

3. **其他要求**：
   - 不允许包含水印或标识
   - 不允许包含文字
   - 不允许包含 NSFW 内容
   - 图像必须清晰可辨

### 图像输入方式

1. **URL 方式**：
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg"
                    }
                }
            ]
        }
    ]
)
```

2. **Base64 编码方式**：
```python
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

base64_image = encode_image("path/to/image.jpg")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
)
```

### 图像细节级别控制

1. **低细节模式**：
```python
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/image.jpg",
        "detail": "low"  # 使用 85 个令牌处理 512px × 512px 的图像
    }
}
```

2. **高细节模式**：
```python
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/image.jpg",
        "detail": "high"  # 使用 170 个令牌处理高分辨率图像
    }
}
```

3. **自动模式**：
```python
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/image.jpg",
        "detail": "auto"  # 默认值，让模型自动决定
    }
}
```

### 性能优化建议

1. **图像预处理**：
   - 在上传前压缩大图像
   - 根据需求调整图像分辨率
   - 移除不必要的元数据

2. **细节级别选择**：
   - 简单识别任务使用 "low" 细节级别
   - 需要详细分析时使用 "high" 细节级别
   - 不确定时使用 "auto" 让模型决定

3. **批量处理优化**：
   - 实现图像缓存机制
   - 使用异步处理多个图像
   - 实现请求限流控制 

### 多图像输入

#### 基本用法
```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "比较这些图片的区别："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image1.jpg"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image2.jpg"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)
```

#### 混合输入示例
```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "第一张图片是什么季节？第二张图片呢？"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/spring.jpg",
                        "detail": "low"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/winter.jpg",
                        "detail": "high"
                    }
                }
            ]
        }
    ]
)
```

### 模型限制

1. **医疗图像**：
   - 不适合解释 CT 扫描、X光片等专业医疗图像
   - 不应用于医疗诊断或建议

2. **非英文文本**：
   - 对非拉丁字母（如日文、韩文）的处理可能不够理想
   - 建议提供清晰的上下文或翻译

3. **文本处理**：
   - 放大图像中的文本以提高可读性
   - 避免裁剪重要的文字信息

4. **图像旋转和方向**：
   - 可能误解旋转或倒置的文本和图像
   - 建议在上传前调整图像方向

5. **视觉元素**：
   - 对复杂图表中的虚线、实线等样式区分可能不够准确
   - 颜色和样式变化的识别可能不够精确

6. **空间推理**：
   - 在需要精确空间定位的任务上表现可能不够理想
   - 例如：棋盘位置识别等

7. **准确性**：
   - 某些场景下可能生成不准确的描述
   - 建议交叉验证重要信息

8. **图像形状**：
   - 全景图和鱼眼图像的处理可能不够理想
   - 建议使用标准视角的图像

9. **元数据处理**：
   - 不处理原始文件名和元数据
   - 图像会在分析前调整大小

10. **计数限制**：
    - 对图像中物体的精确计数可能不够准确
    - 适合提供近似数量估计

11. **验证码限制**：
    - 系统会阻止验证码图片的提交
    - 不支持验证码识别功能

### 成本计算

1. **基本计算规则**：
   - `detail: "low"` 模式：85 个令牌
   - `detail: "high"` 模式：根据图像大小计算

2. **高细节模式计算方法**：
   ```python
   def calculate_high_detail_tokens(image_width, image_height):
       # 步骤 1：缩放到 2048px 范围内
       scale = min(2048 / max(image_width, image_height), 1)
       scaled_width = int(image_width * scale)
       scaled_height = int(image_height * scale)
       
       # 步骤 2：确保短边至少 768px
       if min(scaled_width, scaled_height) < 768:
           scale_up = 768 / min(scaled_width, scaled_height)
           scaled_width = int(scaled_width * scale_up)
           scaled_height = int(scaled_height * scale_up)
       
       # 步骤 3：计算 512px 方块数量
       blocks_x = (scaled_width + 511) // 512
       blocks_y = (scaled_height + 511) // 512
       
       # 步骤 4：计算总令牌数
       total_tokens = blocks_x * blocks_y * 170 + 85
       
       return total_tokens
   ```

3. **示例计算**：
   - 1024×1024 图像：765 个令牌
   - 2048×4096 图像：1105 个令牌
   - 4096×8192 图像（低细节模式）：85 个令牌

4. **优化建议**：
   - 使用适当的细节级别
   - 在上传前调整图像大小
   - 批量处理时考虑总令牌消耗 