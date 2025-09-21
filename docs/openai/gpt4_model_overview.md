# GPT-4 模型概览

## 基本信息
- **模型名称**：GPT-4o
- **类型**：Default
- **描述**：最智能、最灵活的 GPT 模型

## 性能指标
- **智能水平**：High（三点满格）
- **速度**：Medium（两点）
- **价格范围**：$2.5 - $10（每次请求）
- **功能**：支持文本和图像输入

## 主要特性
- 128,000 上下文窗口
- 96,384 最大输出令牌数
- 知识截止日期：2023年10月

## 定价结构
- Input: $2.50
- Cached Input: $1.25
- Output: $10.00

## 支持的功能
### 模态类型
- Text（文本）
- Audio（音频，不支持）

### 端点
1. Chat Completions
2. Assistants
3. Fine-tuning
4. Image generation（不支持）
5. Text-to-speech（不支持）
6. Moderation

### 特性
1. Streaming
2. Structured outputs
3. Function calling
4. Predicted outputs

## 快照版本
- gpt-4o-2024-11-26
- gpt-4o-2024-08-06
- gpt-4o-2024-05-13

## 使用限制
根据不同的用户等级（Tier），有不同的速率限制：

| Tier | TPM | RPM | TPD | BATCH/QUEUE LIMIT |
|------|-----|-----|-----|------------------|
| Free | 500 | - | 30,000 | 90,000 |
| Tier 1 | 1,000 | - | 450,000 | 1,350,000 |
| Tier 2 | 5,000 | - | 600,000 | 50,000,000 |
| Tier 3 | 10,000 | - | 2,000,000 | 200,000,000 |
| Tier 4 | 50,000 | - | 30,000,000 | 5,000,000,000 |

注：
- TPM: Tokens Per Minute（每分钟令牌数）
- RPM: Requests Per Minute（每分钟请求数）
- TPD: Tokens Per Day（每天令牌数） 