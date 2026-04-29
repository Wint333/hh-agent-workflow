from app.domain.schemas import AgentDecision, RequirementState
from app.utils.text import contains_any


class DecisionAgent:
    reset_words = ["重新定制", "重新开始", "重来", "推倒重来", "清空"]
    handoff_words = ["转人工", "人工客服", "找人", "人工接管"]
    generate_words = ["可以出图", "直接出图", "生成图片", "先出一版", "够了", "就这样"]

    def decide(self, text: str, state: RequirementState) -> AgentDecision:
        if contains_any(text, self.reset_words):
            return AgentDecision(
                action="reset",
                reply_text="上一版内容已经清空，我们可以从新的定制方向重新开始。",
                confidence=1.0,
                reason="user_requested_reset",
            )

        if contains_any(text, self.handoff_words):
            return AgentDecision(
                action="handoff",
                reply_text="好的，这条需求我会标记为需要人工接管，方便后续进一步沟通报价和打样细节。",
                confidence=1.0,
                reason="user_requested_handoff",
            )

        missing = state.missing_required_fields()
        user_wants_generation = contains_any(text, self.generate_words)

        if not missing and (state.completion_score() >= 0.72 or user_wants_generation):
            return AgentDecision(
                action="generate_preview",
                reply_text="信息已经比较清晰，我先根据当前需求生成一版企业礼赠纸雕笔记本视觉方案。",
                missing_fields=[],
                confidence=0.88,
                reason="requirements_ready",
            )

        if user_wants_generation and len(missing) <= 1:
            return AgentDecision(
                action="generate_preview",
                reply_text="目前关键信息基本够用，我先生成一版，后续可以继续按反馈调整。",
                missing_fields=missing,
                confidence=0.78,
                reason="user_requested_generation_with_minor_missing",
            )

        ask_text = self._build_ask_text(missing)
        return AgentDecision(
            action="ask_more",
            reply_text=ask_text,
            missing_fields=missing,
            confidence=0.65,
            reason="need_more_information",
        )

    def _build_ask_text(self, missing: list[str]) -> str:
        if not missing:
            return "可以再补充一下想要的颜色、辅助元素或不希望出现的风格，我会据此整理首图方案。"
        if len(missing) == 1:
            return f"还差一个关键信息：{missing[0]}。补充后我就可以进入首图方案生成。"
        return "为了避免首图偏差，还需要补充：" + "、".join(missing[:3]) + "。"
