# 获取聊天补全 API

## 概述
获取已存储的聊天补全。只有在创建时设置了 `store` 参数为 `true` 的聊天补全才能被检索。

## API 端点
```
GET https://api.openai.com/v1/chat/completions/{completion_id}
```

## 路径参数

### completion_id
- **类型**：string
- **必需**：是
- **描述**：要检索的聊天补全的 ID

## 返回值

返回与指定 ID 匹配的 ChatCompletion 对象。返回的对象结构如下：

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

## 使用说明

1. 此 API 只能获取已存储的聊天补全
2. 要使聊天补全可检索，创建时必须设置 `store: true`
3. 如果指定的 ID 不存在或未存储，API 将返回错误
4. 返回的对象格式与创建聊天补全时的响应格式相同

## 错误处理

可能的错误情况包括：
- 指定的补全 ID 不存在
- 补全未被存储（创建时未设置 `store: true`）
- 认证失败
- 权限不足

## 相关 API
- [创建聊天补全](chat_completion_api.md) - 用于创建新的聊天补全
- [列出聊天补全]() - 用于列出所有已存储的聊天补全 