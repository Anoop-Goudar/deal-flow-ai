from __future__ import annotations

from models import ProductRecommendation, Task
from state import store


class TaskRouter:
    def create_task(self, client_id: str, recommendation: ProductRecommendation) -> Task:
        task = Task(
            task_id=store.next_task_id(),
            client_id=client_id,
            product=recommendation.product,
            assigned_to=recommendation.assigned_agent,
            action=recommendation.next_action,
            status="pending",
        )
        store.tasks.append(task)
        return task
