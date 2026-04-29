# Architecture

```text
Customer / Feige / Douyin
        |
        v
API Gateway: /api/chat
        |
        v
BrainService
  ├─ RequirementAgent       自然语言 -> 结构化需求字段
  ├─ DecisionAgent          判断追问 / 生成 / 重置 / 人工接管
  ├─ PromptCompilerAgent    结构化需求 -> 图像 Prompt
  ├─ QualityAgent           生成前规则质检
  └─ AnalyticsService       业务事件沉淀
        |
        v
ImageClient -> generated image URL
        |
        v
Outbox Queue -> Channel Worker -> Customer
```

## Data Flow

1. 渠道 Worker 收到客户消息。
2. Worker 调用 `/api/chat`。
3. BrainService 读取历史会话状态。
4. RequirementAgent 更新结构化需求字段。
5. DecisionAgent 判断下一步动作。
6. 若触发生成，PromptCompilerAgent 编译图像 prompt。
7. ImageClient 生成 mock 图片或调用真实模型。
8. 回复文本和图片进入 outbox。
9. Worker 轮询 `/api/outbox/pending` 并回传客户。
10. AnalyticsService 记录业务事件，用于统计和优化。
