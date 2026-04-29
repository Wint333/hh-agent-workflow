import pytest

from app.domain.schemas import ChatRequest
from app.services.brain_service import BrainService
from app.storage.sqlite_store import SQLiteStore


@pytest.mark.asyncio
async def test_brain_service_generates_preview(tmp_path):
    db_path = tmp_path / "test.db"
    store = SQLiteStore(db_path=db_path)
    brain = BrainService(store)

    first = await brain.handle_chat(
        ChatRequest(
            user_id="u1",
            text="我们是AsterCraft Studio，想做客户答谢礼，主体放山峰和海浪，蓝色为主，高级商务风",
        )
    )
    assert first.requirement_state.business_or_product is not None

    second = await brain.handle_chat(
        ChatRequest(
            user_id="u1",
            text="不要卡通，可以出图",
        )
    )
    assert second.action == "generate_preview"
    assert second.generated_image_url is not None
    assert len(second.outbox_task_ids) >= 2
