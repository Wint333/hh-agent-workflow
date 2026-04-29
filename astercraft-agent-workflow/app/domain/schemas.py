from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="渠道侧用户 ID")
    text: str = Field(..., min_length=1, description="客户输入内容")
    product_name: Optional[str] = Field(default="3D立体镂空纸雕笔记本")


class RequirementState(BaseModel):
    business_or_product: Optional[str] = None
    gift_use_case: Optional[str] = None
    confirmed_main_objects: List[str] = Field(default_factory=list)
    confirmed_supporting_elements: List[str] = Field(default_factory=list)
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    visual_mood: Optional[str] = None
    forbidden_elements: List[str] = Field(default_factory=list)
    main_position_note: Optional[str] = None
    extra_notes: List[str] = Field(default_factory=list)

    def completion_score(self) -> float:
        required = [
            bool(self.business_or_product),
            bool(self.gift_use_case),
            bool(self.confirmed_main_objects),
            bool(self.visual_mood),
        ]
        optional = [
            bool(self.confirmed_supporting_elements),
            bool(self.primary_color),
            bool(self.forbidden_elements),
            bool(self.main_position_note),
        ]
        return round((sum(required) * 0.18 + sum(optional) * 0.07), 2)

    def missing_required_fields(self) -> List[str]:
        missing = []
        if not self.business_or_product:
            missing.append("品牌/业务信息")
        if not self.gift_use_case:
            missing.append("礼赠用途")
        if not self.confirmed_main_objects:
            missing.append("核心纸雕主体")
        if not self.visual_mood:
            missing.append("整体风格氛围")
        return missing


class AgentDecision(BaseModel):
    action: str = Field(..., description="ask_more | generate_preview | reset | handoff")
    reply_text: str
    missing_fields: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""


class OutboxTask(BaseModel):
    id: str
    user_id: str
    type: str
    content: str
    status: str
    created_at: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    user_id: str
    action: str
    reply_text: str
    requirement_state: RequirementState
    generated_image_url: Optional[str] = None
    outbox_task_ids: List[str] = Field(default_factory=list)
    analytics: Dict[str, Any] = Field(default_factory=dict)


class StatsSummary(BaseModel):
    total_sessions: int
    total_messages: int
    total_generation_tasks: int
    image_success_count: int
    handoff_count: int
    reset_count: int
    average_completion_score: float
    top_missing_fields: Dict[str, int]
