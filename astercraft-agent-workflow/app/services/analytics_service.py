from collections import Counter
from typing import Any, Dict, Optional

from app.domain.schemas import RequirementState, StatsSummary
from app.storage.sqlite_store import SQLiteStore


class AnalyticsService:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def record_message(self, user_id: str, state: RequirementState, decision: str, missing_fields: list[str]) -> None:
        self.store.record_event(
            "message_processed",
            {
                "completion_score": state.completion_score(),
                "decision": decision,
                "missing_fields": missing_fields,
            },
            user_id=user_id,
        )

    def record_generation(self, user_id: str, image_url: Optional[str], quality: Dict[str, Any]) -> None:
        self.store.record_event(
            "generation_task",
            {
                "success": bool(image_url),
                "image_url": image_url,
                "quality": quality,
            },
            user_id=user_id,
        )

    def record_handoff(self, user_id: str) -> None:
        self.store.record_event("handoff", {}, user_id=user_id)

    def record_reset(self, user_id: str) -> None:
        self.store.record_event("reset", {}, user_id=user_id)

    def summary(self) -> StatsSummary:
        message_events = self.store.fetch_events(["message_processed"])
        generation_events = self.store.fetch_events(["generation_task"])
        handoff_events = self.store.fetch_events(["handoff"])
        reset_events = self.store.fetch_events(["reset"])

        scores = [float(e["payload"].get("completion_score", 0)) for e in message_events]
        missing_counter: Counter[str] = Counter()
        for e in message_events:
            missing_counter.update(e["payload"].get("missing_fields", []))

        image_success_count = sum(1 for e in generation_events if e["payload"].get("success"))

        return StatsSummary(
            total_sessions=self.store.count_rows("sessions"),
            total_messages=self.store.count_rows("messages"),
            total_generation_tasks=len(generation_events),
            image_success_count=image_success_count,
            handoff_count=len(handoff_events),
            reset_count=len(reset_events),
            average_completion_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            top_missing_fields=dict(missing_counter.most_common(8)),
        )
