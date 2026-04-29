import uuid
from typing import Any, Dict, List

from app.domain.schemas import OutboxTask
from app.storage.sqlite_store import SQLiteStore


class OutboxService:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def enqueue_text(self, user_id: str, content: str, meta: Dict[str, Any] | None = None) -> str:
        task_id = uuid.uuid4().hex
        self.store.create_outbox_task(task_id, user_id, "text", content, meta or {})
        return task_id

    def enqueue_image(self, user_id: str, image_url: str, meta: Dict[str, Any] | None = None) -> str:
        task_id = uuid.uuid4().hex
        self.store.create_outbox_task(task_id, user_id, "image", image_url, meta or {})
        return task_id

    def pending(self, limit: int = 20) -> List[OutboxTask]:
        return [OutboxTask(**row) for row in self.store.list_pending_outbox(limit=limit)]

    def ack(self, task_id: str) -> bool:
        return self.store.ack_outbox(task_id)
