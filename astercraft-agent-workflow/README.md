# AsterCraft Agent Workflow

面向印刷与企业礼赠定制场景的 AI 驱动业务工作流系统示例工程。

这个项目不是单纯的聊天机器人，而是把客户咨询、需求结构化、视觉方案生成、渠道回传和业务统计串成一个完整闭环。它适合用于展示 Agent / AI Workflow 的真实业务落地思路。

## 核心能力

1. **多轮需求理解**
   - 自动识别客户提供的品牌、礼赠用途、核心视觉主体、辅助元素、色彩、风格、禁用元素等字段。
   - 保存会话上下文，避免重复追问。

2. **Agent 决策流**
   - Requirement Agent：抽取结构化需求。
   - Decision Agent：判断继续追问、触发首图生成、重新定制或人工接管。
   - Prompt Compiler Agent：将业务需求编译为高质量图像生成 Prompt。
   - Quality Agent：对生成任务做基础可制造性检查。
   - Analytics Agent：沉淀业务数据，用于后续优化转化。

3. **图像生成工作流**
   - 默认使用本地 Mock 图像生成，方便审核和演示。
   - 支持通过环境变量接入 OpenAI-compatible / 聚合图像接口。
   - 生成结果写入 outbox 队列，由 Worker 回传给渠道。

4. **业务统计闭环**
   - 记录咨询次数、字段收集完整度、生成触发次数、图片成功率、人工接管次数、重新定制次数等指标。
   - 提供 `/api/stats/summary` 接口查看业务漏斗。

5. **工程结构**
   - FastAPI 后端
   - SQLite 本地持久化
   - Outbox 队列
   - 可扩展 Agent 服务层
   - 示例渠道 Worker
   - Pytest 基础测试

## 快速启动

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

浏览器访问：

```text
http://127.0.0.1:8000/docs
```

## 本地测试

```bash
pytest -q
```

## 示例请求

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-001",
    "text": "我们是AsterCraft Studio，想做一个给客户送礼的纸雕笔记本，主体放山峰和海浪，风格高级一点，蓝色为主"
  }'
```

继续补充：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user-001",
    "text": "用途是企业客户答谢，禁用卡通风，可以出图"
  }'
```

查看待发送队列：

```bash
curl http://127.0.0.1:8000/api/outbox/pending
```

查看业务统计：

```bash
curl http://127.0.0.1:8000/api/stats/summary
```

## 环境变量

见 `.env.example`。

默认不需要任何外部模型 Key，系统会使用本地规则和 Mock 图像生成，方便运行和审核。接入真实模型时，配置 `CHAT_API_KEY`、`CHAT_BASE_URL`、`CHAT_MODEL`、`IMAGE_API_KEY`、`IMAGE_BASE_URL`、`IMAGE_MODEL` 即可。

## 适合审核时说明的亮点

- 项目解决的不是闲聊问题，而是企业定制业务中“需求模糊、沟通链路长、设计首图慢、数据难沉淀”的问题。
- Agent 不只负责回复，还会参与需求抽取、信息完整度判断、图像 Prompt 编译、任务队列回传和业务统计。
- 后续可拆分为需求理解 Agent、视觉设计 Agent、报价 Agent、质检 Agent、运营分析 Agent。
- 项目对文本推理、长上下文分析、图像生成和数据分析额度都有真实需求。
