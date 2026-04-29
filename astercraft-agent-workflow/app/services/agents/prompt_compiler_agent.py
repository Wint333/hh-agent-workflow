from app.domain.schemas import RequirementState


class PromptCompilerAgent:
    """将结构化业务需求编译成图像模型更容易理解的视觉 Prompt。"""

    def compile(self, state: RequirementState) -> str:
        main_objects = "、".join(state.confirmed_main_objects) or "品牌核心意象"
        supporting = "、".join(state.confirmed_supporting_elements) or "轻量级文化纹样与空间层次"
        forbidden = "、".join(state.forbidden_elements) or "避免塑料感、玩具感、廉价感、文字乱码"

        return f"""
Create a premium realistic product photography image of a 3D hollow paper-carving notebook for enterprise gift customization.

Business / brand context: {state.business_or_product or "enterprise brand"}.
Gift use case: {state.gift_use_case or "business gift"}.
Main paper-carving objects: {main_objects}.
Supporting elements: {supporting}.
Primary color: {state.primary_color or "elegant brand color"}.
Secondary color: {state.secondary_color or "subtle neutral color"}.
Visual mood: {state.visual_mood or "premium, elegant, manufacturable"}.
Composition note: {state.main_position_note or "upper window structure, lower cover remains usable and clean"}.
Forbidden elements: {forbidden}.

Hard constraints:
- exactly one notebook only, no collage, no split screen
- visible layered paper structure, tunnel-book depth, at least 8 paper layers
- every paper layer contributes different depth information
- not a shallow relief, not a plastic sculpture, not a floating decoration
- the paper carving must be physically connected with the notebook
- realistic lighting, high-end product photography, clear material texture
- keep the cover practical and manufacturable
""".strip()
