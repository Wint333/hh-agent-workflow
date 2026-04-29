import html
import uuid

from app.core.config import get_settings


class ImageClient:
    """图像生成客户端。

    默认使用本地 SVG mock，确保项目无需外部密钥即可运行。
    生产环境可在这里接入真实图像生成接口。
    """

    def __init__(self):
        self.settings = get_settings()

    async def generate(self, prompt: str, user_id: str) -> dict:
        if self.settings.image_provider.lower() == "mock":
            return self._generate_mock_svg(prompt, user_id)

        # 这里保留 OpenAI-compatible 图像接口接入位置。
        # 为避免审核仓库泄露密钥，示例工程不内置任何真实 key。
        return self._generate_mock_svg(prompt, user_id, provider_note="external_provider_not_configured")

    def _generate_mock_svg(self, prompt: str, user_id: str, provider_note: str = "mock") -> dict:
        image_id = f"{uuid.uuid4().hex}.svg"
        path = self.settings.image_dir_path / image_id
        summary = html.escape(prompt[:260])
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <rect width="1200" height="800" fill="#f6f1e8"/>
  <rect x="250" y="120" width="700" height="520" rx="36" fill="#ffffff" stroke="#1f2937" stroke-width="6"/>
  <rect x="330" y="170" width="540" height="260" rx="28" fill="#e8f0f7" stroke="#64748b" stroke-width="4"/>
  <path d="M360 390 C430 280, 510 315, 570 240 C660 360, 735 260, 845 390" fill="none" stroke="#0f172a" stroke-width="18" stroke-linecap="round"/>
  <path d="M360 390 C460 430, 545 355, 635 400 C720 440, 785 380, 845 405" fill="none" stroke="#2563eb" stroke-width="14" stroke-linecap="round"/>
  <g opacity="0.55">
    <rect x="345" y="185" width="510" height="230" rx="24" fill="none" stroke="#94a3b8" stroke-width="6"/>
    <rect x="360" y="200" width="480" height="200" rx="22" fill="none" stroke="#cbd5e1" stroke-width="5"/>
    <rect x="375" y="215" width="450" height="170" rx="20" fill="none" stroke="#e2e8f0" stroke-width="4"/>
  </g>
  <text x="600" y="510" text-anchor="middle" font-family="Arial, sans-serif" font-size="34" fill="#111827">AsterCraft Agent Preview</text>
  <text x="600" y="560" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#475569">3D paper-carving notebook concept mock</text>
  <foreignObject x="300" y="660" width="600" height="90">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial;font-size:18px;color:#475569;text-align:center;">{summary}</div>
  </foreignObject>
</svg>"""
        path.write_text(svg, encoding="utf-8")

        public_url = f"{self.settings.public_base_url.rstrip('/')}/images/{image_id}"
        return {
            "image_url": public_url,
            "local_path": str(path),
            "provider": provider_note,
            "image_id": image_id,
        }
