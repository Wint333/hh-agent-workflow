from app.domain.schemas import ChatRequest, ChatResponse, RequirementState
from app.services.agents.decision_agent import DecisionAgent
from app.services.agents.prompt_compiler_agent import PromptCompilerAgent
from app.services.agents.quality_agent import QualityAgent
from app.services.agents.requirement_agent import RequirementAgent
from app.services.analytics_service import AnalyticsService
from app.services.image_client import ImageClient
from app.services.outbox_service import OutboxService
from app.storage.sqlite_store import SQLiteStore


class BrainService:
    def __init__(self, store: SQLiteStore):
        self.store = store
        self.requirement_agent = RequirementAgent()
        self.decision_agent = DecisionAgent()
        self.prompt_compiler = PromptCompilerAgent()
        self.quality_agent = QualityAgent()
        self.image_client = ImageClient()
        self.outbox = OutboxService(store)
        self.analytics = AnalyticsService(store)

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        raw_state = self.store.get_session_state(request.user_id)
        state = RequirementState(**raw_state) if raw_state else RequirementState()

        self.store.add_message(request.user_id, "user", request.text)

        # 先判断是否显式重置，避免旧上下文污染新需求。
        pre_decision = self.decision_agent.decide(request.text, state)
        if pre_decision.action == "reset":
            new_state = RequirementState()
            self.store.reset_session(request.user_id, new_state.model_dump())
            self.store.add_message(request.user_id, "assistant", pre_decision.reply_text)
            task_id = self.outbox.enqueue_text(request.user_id, pre_decision.reply_text, {"action": "reset"})
            self.analytics.record_reset(request.user_id)
            self.analytics.record_message(request.user_id, new_state, "reset", [])
            return ChatResponse(
                user_id=request.user_id,
                action="reset",
                reply_text=pre_decision.reply_text,
                requirement_state=new_state,
                outbox_task_ids=[task_id],
                analytics={"completion_score": new_state.completion_score()},
            )

        state = self.requirement_agent.update_state(state, request.text, request.product_name)
        decision = self.decision_agent.decide(request.text, state)

        self.store.upsert_session_state(request.user_id, state.model_dump())

        outbox_task_ids: list[str] = []
        generated_image_url = None

        if decision.action == "handoff":
            self.analytics.record_handoff(request.user_id)
            task_id = self.outbox.enqueue_text(request.user_id, decision.reply_text, {"action": "handoff"})
            outbox_task_ids.append(task_id)

        elif decision.action == "generate_preview":
            prompt = self.prompt_compiler.compile(state)
            quality = self.quality_agent.inspect_prompt(state, prompt)
            image_result = await self.image_client.generate(prompt=prompt, user_id=request.user_id)
            generated_image_url = image_result["image_url"]

            text_task_id = self.outbox.enqueue_text(
                request.user_id,
                decision.reply_text + " 生成后如需调整，可以继续补充修改意见。",
                {"action": "generate_preview", "quality": quality},
            )
            image_task_id = self.outbox.enqueue_image(
                request.user_id,
                generated_image_url,
                {"prompt": prompt, "quality": quality, "image_result": image_result},
            )
            outbox_task_ids.extend([text_task_id, image_task_id])
            self.analytics.record_generation(request.user_id, generated_image_url, quality)

        else:
            task_id = self.outbox.enqueue_text(
                request.user_id,
                decision.reply_text,
                {"action": "ask_more", "missing_fields": decision.missing_fields},
            )
            outbox_task_ids.append(task_id)

        self.store.add_message(request.user_id, "assistant", decision.reply_text)
        self.analytics.record_message(request.user_id, state, decision.action, decision.missing_fields)

        return ChatResponse(
            user_id=request.user_id,
            action=decision.action,
            reply_text=decision.reply_text,
            requirement_state=state,
            generated_image_url=generated_image_url,
            outbox_task_ids=outbox_task_ids,
            analytics={"completion_score": state.completion_score(), "missing_fields": decision.missing_fields},
        )
