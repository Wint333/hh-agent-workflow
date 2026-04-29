import re
from typing import List

from app.domain.schemas import RequirementState
from app.utils.text import normalize_text, unique_merge


class RequirementAgent:
    """把客户自然语言整理成可追踪的结构化需求字段。"""

    color_words = ["红", "橙", "黄", "绿", "青", "蓝", "紫", "黑", "白", "金", "银", "灰", "粉", "棕"]
    mood_words = ["高级", "科技", "中式", "国潮", "简约", "商务", "温暖", "大气", "精致", "复古", "现代", "典雅", "年轻"]
    use_case_words = ["客户答谢", "员工福利", "会议伴手礼", "展会", "开业", "周年庆", "商务礼赠", "节日礼品", "年会", "招商"]

    def update_state(self, current: RequirementState, text: str, product_name: str | None = None) -> RequirementState:
        text = normalize_text(text)
        state = current.model_copy(deep=True)

        business = self._extract_business(text)
        if business:
            state.business_or_product = business
        elif product_name and not state.business_or_product:
            state.business_or_product = product_name

        use_case = self._extract_use_case(text)
        if use_case:
            state.gift_use_case = use_case

        main_objects = self._extract_main_objects(text)
        if main_objects:
            state.confirmed_main_objects = unique_merge(state.confirmed_main_objects, main_objects)

        supporting = self._extract_supporting_elements(text)
        if supporting:
            state.confirmed_supporting_elements = unique_merge(state.confirmed_supporting_elements, supporting)

        colors = self._extract_colors(text)
        if colors:
            state.primary_color = state.primary_color or colors[0]
            if len(colors) > 1:
                state.secondary_color = state.secondary_color or colors[1]

        mood = self._extract_mood(text)
        if mood:
            state.visual_mood = mood

        forbidden = self._extract_forbidden(text)
        if forbidden:
            state.forbidden_elements = unique_merge(state.forbidden_elements, forbidden)

        position_note = self._extract_position(text)
        if position_note:
            state.main_position_note = position_note

        if len(text) > 8:
            state.extra_notes = unique_merge(state.extra_notes, [text])

        return state

    def _extract_business(self, text: str) -> str | None:
        patterns = [
            r"我们是([^，。,. ]{2,20})",
            r"公司叫([^，。,. ]{2,20})",
            r"品牌叫([^，。,. ]{2,20})",
            r"我是([^，。,. ]{2,20})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1)
        return None

    def _extract_use_case(self, text: str) -> str | None:
        for word in self.use_case_words:
            if word in text:
                return word
        if "送客户" in text or "客户送礼" in text:
            return "客户答谢"
        if "送员工" in text:
            return "员工福利"
        return None

    def _extract_main_objects(self, text: str) -> List[str]:
        candidates = []
        object_words = [
            "山峰", "海浪", "海", "船", "城市", "建筑", "工厂", "机器", "印刷机", "纸张",
            "龙", "云", "桥", "树", "花", "书", "灯塔", "河流", "长城", "熊猫", "产品"
        ]
        for word in object_words:
            if word in text:
                candidates.append(word)
        m = re.search(r"主体(?:放|是|要)?([^，。,.]{2,30})", text)
        if m:
            candidates.extend(re.split(r"[和、,， ]+", m.group(1)))
        return [x for x in candidates if x]

    def _extract_supporting_elements(self, text: str) -> List[str]:
        results = []
        m = re.search(r"(?:辅助元素|周围|旁边|配)(?:放|加|要)?([^。,.，]{2,40})", text)
        if m:
            results.extend(re.split(r"[和、,， ]+", m.group(1)))
        for word in ["云纹", "水纹", "星光", "丝带", "企业logo", "logo", "纹样", "文字区"]:
            if word in text:
                results.append(word)
        return [x for x in results if x]

    def _extract_colors(self, text: str) -> List[str]:
        results = []
        for word in self.color_words:
            if f"{word}色" in text or f"{word}为主" in text:
                results.append(f"{word}色")
        return results

    def _extract_mood(self, text: str) -> str | None:
        found = [word for word in self.mood_words if word in text]
        if found:
            return "、".join(found[:3])
        return None

    def _extract_forbidden(self, text: str) -> List[str]:
        results = []
        patterns = [
            r"不要([^，。,.]{1,20})",
            r"禁用([^，。,.]{1,20})",
            r"不能有([^，。,.]{1,20})",
            r"避免([^，。,.]{1,20})",
        ]
        for pattern in patterns:
            for m in re.finditer(pattern, text):
                results.extend(re.split(r"[和、,， ]+", m.group(1)))
        return [x for x in results if x]

    def _extract_position(self, text: str) -> str | None:
        if "上方开窗" in text:
            return "上方开窗，下方保留完整封面"
        if "下半区" in text and "保留" in text:
            return "下半区保留大面积完整封面"
        if "居中" in text:
            return "主体居中但避免相框感"
        return None
