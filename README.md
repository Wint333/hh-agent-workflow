# hh-agent-workflow
该系统底层基于 OpenClaw 的 Agent 编排思路进行设计，业务侧使用 FastAPI 构建 API 服务和状态管理模块，通过 LLM API 完成客户需求理解、字段抽取和多轮对话决策，通过图像生成 API 完成视觉方案生成，并结合 Playwright Worker 对接飞鸽/抖店客服页面，实现从客户咨询到方案回传的自动化闭环。
