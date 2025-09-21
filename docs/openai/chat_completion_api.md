# Chat Completion API

## 概述
给定一个由消息组成的对话列表，模型将返回响应。相关功能可以参考 Completions。

## API 端点
```
POST https://api.openai.com/v1/chat/completions
```

## 请求参数

### 必需参数

#### messages
- **类型**：array
- **必需**：是
- **描述**：包含对话历史的消息列表
- **支持的消息类型**：
  - text（文本）
  - images（图片）
  - audio（音频）
- **说明**：根据使用的模型不同，支持的消息类型（模态）可能不同

#### model
- **类型**：string
- **必需**：是
- **描述**：指定要使用的模型 ID
- **说明**：具体支持的模型请参考模型兼容性表格

### 可选参数

#### metadata
- **类型**：map
- **必需**：否
- **描述**：可以附加到对象的16个键值对集合
- **限制**：
  - 键：最大长度64个字符的字符串
  - 值：最大长度512个字符的字符串
- **用途**：用于以结构化格式存储对象的附加信息，可通过 API 或仪表板查询对象

#### frequency_penalty
- **类型**：number 或 null
- **必需**：否
- **默认值**：0
- **范围**：-2.0 到 2.0
- **描述**：基于现有文本中的频率对新令牌进行惩罚，正值会降低模型逐字重复相同行的可能性

#### logit_bias
- **类型**：map
- **必需**：否
- **默认值**：null
- **描述**：修改指定令牌在补全中出现的可能性
- **详细说明**：
  - 接受将令牌（由其在分词器中的令牌ID指定）映射到偏差值的 JSON 对象
  - 偏差值范围：-100 到 100
  - 数学上，偏差在采样前添加到模型生成的 logits 中
  - -1 到 1 之间的值会降低或增加选择的可能性
  - -100 或 100 的值会导致禁止或强制选择相关令牌

#### logprobs
- **类型**：boolean 或 null
- **必需**：否
- **默认值**：false
- **描述**：是否返回输出令牌的对数概率
- **说明**：如果为 true，将在消息的 content 中返回每个输出令牌的对数概率

#### top_logprobs
- **类型**：integer 或 null
- **必需**：否
- **描述**：指定在每个令牌位置返回最可能的令牌数量（0-20）
- **要求**：使用此参数时必须将 logprobs 设置为 true
- **范围**：0 到 20

#### max_completion_tokens
- **类型**：integer 或 null
- **必需**：否
- **描述**：可以为补全生成的令牌数量的上限
- **说明**：包括可见的输出令牌和推理令牌

#### store
- **类型**：boolean 或 null
- **默认值**：false
- **描述**：是否存储此次聊天完成请求的输出，用于模型提炼或评估
- **相关功能**：
  - model distillation（模型提炼）
  - evals（评估）

#### reasoning_effort
- **类型**：string 或 null
- **默认值**：medium
- **适用模型**：仅适用于 o1 和 o3-mini 模型
- **描述**：约束推理的努力程度
- **支持的值**：
  - low（低）
  - medium（中）
  - high（高）
- **说明**：降低推理努力可能导致更快的响应速度，但会减少用于推理的令牌数量

#### modalities
- **类型**：array 或 null
- **必需**：否
- **默认值**：`["text"]`
- **描述**：指定此请求要生成的输出类型
- **支持的值**：
  - `["text"]`（默认）
  - `["text", "audio"]`（使用 gpt-4o-audio-preview 模型时）
- **说明**：大多数模型默认只能生成文本，但某些特殊模型可以生成其他类型的输出

#### prediction
- **类型**：object
- **必需**：否
- **描述**：预测输出配置，用于在已知大部分响应内容时提高响应速度
- **使用场景**：当重新生成一个只有少量内容变化的文件时特别有用
- **说明**：通过 Predicted Output 功能可以显著改善响应时间

#### audio
- **类型**：object 或 null
- **必需**：否
- **描述**：音频输出的参数配置
- **使用条件**：当 `modalities` 包含 `"audio"` 时必需
- **说明**：更多详细信息请参考音频生成文档

#### presence_penalty
- **类型**：number 或 null
- **必需**：否
- **默认值**：0
- **范围**：-2.0 到 2.0
- **描述**：基于是否出现在文本中对新令牌进行惩罚，正值会增加模型谈论新主题的可能性

#### response_format
- **类型**：object
- **必需**：否
- **描述**：指定模型必须输出的格式
- **选项**：
  1. JSON Schema 格式：
     ```json
     { "type": "json_schema", "json_schema": {...} }
     ```
     - 启用结构化输出
     - 确保模型输出匹配指定的 JSON schema
     - 详细信息请参考结构化输出指南

  2. JSON 对象格式：
     ```json
     { "type": "json_object" }
     ```
     - 启用 JSON 模式
     - 确保模型生成有效的 JSON

- **重要说明**：
  1. 使用 JSON 模式时，必须通过系统或用户消息明确指示模型生成 JSON
  2. 如果不提供明确指示：
     - 模型可能生成无限的空白
     - 可能在达到令牌限制时导致请求看似"卡住"
  3. 当 `finish_reason="length"` 时：
     - 消息内容可能被截断
     - 可能是由于超出 `max_tokens` 限制
     - 或超出最大上下文长度

#### seed
- **类型**：integer 或 null
- **必需**：否
- **状态**：Beta
- **描述**：用于确定性采样的种子值
- **说明**：
  - 使用相同的 seed 和参数进行重复请求应返回相同结果
  - 确定性不能保证，请使用 `system_fingerprint` 响应参数监控后端变化
  
#### service_tier
- **类型**：string 或 null
- **必需**：否
- **默认值**：auto
- **描述**：指定处理请求的延迟层级
- **选项**：
  - `auto`：
    - 如果项目启用了 Scale tier，将使用 scale tier 信用直到用完
    - 如果项目未启用 Scale tier，将使用默认服务层（较低的正常运行时间 SLA，无延迟保证）
  - `default`：使用默认服务层（较低的正常运行时间 SLA，无延迟保证）

#### stop
- **类型**：string / array / null
- **必需**：否
- **默认值**：null
- **描述**：最多4个序列，当API遇到这些序列时将停止生成更多令牌

#### stream
- **类型**：boolean 或 null
- **必需**：否
- **默认值**：false
- **描述**：是否启用消息增量发送
- **说明**：
  - 启用后，令牌将通过 data-only server-sent events 发送
  - 流将以 `data: [DONE]` 消息结束
  - 参考示例 Python 代码了解具体用法

#### stream_options
- **类型**：object 或 null
- **必需**：否
- **默认值**：null
- **描述**：流式响应的选项配置
- **使用条件**：仅当 `stream: true` 时设置

#### temperature
- **类型**：number 或 null
- **必需**：否
- **默认值**：1
- **范围**：0 到 2
- **描述**：采样温度控制
- **说明**：
  - 较高的值（如 0.8）会使输出更随机
  - 较低的值（如 0.2）会使输出更确定和集中
  - 建议只调整此参数或 top_p，而不是同时调整两者

#### top_p
- **类型**：number 或 null
- **必需**：否
- **默认值**：1
- **描述**：核采样（nucleus sampling）的概率质量阈值
- **说明**：
  - 模型只考虑 top_p 概率质量的令牌
  - 例如：0.1 表示只考虑概率质量前 10% 的令牌
  - 建议只调整此参数或 temperature，而不是同时调整两者

#### tool_choice
- **类型**：string 或 object
- **必需**：否
- **描述**：控制模型如何使用工具
- **选项**：
  - `none`：模型不会调用任何工具，而是生成消息（无工具时的默认值）
  - `auto`：模型可以选择生成消息或调用一个或多个工具（有工具时的默认值）
  - `required`：模型必须调用一个或多个工具
  - 特定工具：使用格式 `{"type": "function", "function": {"name": "my_function"}}` 强制模型调用指定工具

#### parallel_tool_calls
- **类型**：boolean
- **必需**：否
- **默认值**：true
- **描述**：是否在工具使用期间启用并行函数调用

#### user
- **类型**：string
- **必需**：否
- **描述**：表示最终用户的唯一标识符
- **用途**：帮助 OpenAI 监控和检测滥用行为

## 已废弃参数

以下参数已被废弃，请使用推荐的替代参数：

1. function_call → 使用 tool_choice
2. functions → 使用 tools
3. max_tokens → 使用 max_completion_tokens

## 返回值

API 返回一个 chat completion 对象，或在启用流式传输时返回 chat completion chunk 对象序列。

### Chat Completion 对象
```json
{
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "消息内容",
            "tool_calls": [{
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": "{\"location\": \"北京\", \"unit\": \"celsius\"}"
                }
            }]
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 123,
        "completion_tokens": 456,
        "total_tokens": 579
    }
}
```

### 流式响应
当启用 stream 参数时，API 会返回一系列 chat completion chunk 对象，每个对象包含部分响应内容。

## 注意事项
1. 参数支持可能因模型而异，特别是对于较新的推理模型
2. 对于推理模型中不支持的参数，请参考推理指南
3. 不同的消息类型支持取决于所使用的具体模型
4. 某些参数（如 max_tokens）已被新参数替代，使用时需注意兼容性
5. 使用高级功能（如 logprobs）时需注意相关参数的依赖关系
6. 使用 JSON 输出格式时，需要特别注意提供明确的指示，以避免生成问题
7. 音频输出功能仅支持特定模型
8. temperature 和 top_p 是互斥的采样控制参数，建议只调整其中之一
9. 使用 seed 参数时要注意其 Beta 状态，并监控 system_fingerprint 以确保一致性
10. 使用流式响应时，确保正确处理 server-sent events 
11. 使用工具调用时，建议使用 parallel_tool_calls 参数来优化性能
12. 在使用 user 参数时，确保提供一致的标识符以便于跟踪和监控
13. 注意已废弃参数的替代方案，及时更新代码以使用新参数 