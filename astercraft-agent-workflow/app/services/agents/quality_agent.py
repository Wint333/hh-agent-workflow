from app.domain.schemas import RequirementState


class QualityAgent:
    """生成前做基础可制造性检查。真实环境中可替换为视觉质检模型。"""

    def inspect_prompt(self, state: RequirementState, prompt: str) -> dict:
        risks = []
        if len(state.confirmed_main_objects) > 4:
            risks.append("核心主体过多，纸雕窗口可能显得拥挤")
        if not state.main_position_note:
            risks.append("未明确开窗位置，默认采用上方开窗")
        if "文字" in prompt and "乱码" not in prompt:
            risks.append("包含文字元素时需避免模型生成不可读文字")

        return {
            "passed": len(risks) <= 2,
            "risks": risks,
            "manufacturability_note": "当前方案适合作为首图概念图，打样前还需要设计师确认刀线、层数和纸张工艺。",
        }
