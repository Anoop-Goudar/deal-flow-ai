from __future__ import annotations

from copy import deepcopy

from mock_data import seed_clients, seed_conversations, seed_policies
from models import AppStateSnapshot, Client, ConversationEvent, PipelineResult, Task


class InMemoryStateStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.clients: dict[str, Client] = seed_clients()
        self.conversations: dict[str, list[ConversationEvent]] = seed_conversations()
        self.policies = seed_policies()
        self.recommendations: dict[str, PipelineResult] = {}
        self.tasks: list[Task] = []
        self._task_counter = 100

    def next_task_id(self) -> str:
        self._task_counter += 1
        return f"T{self._task_counter}"

    def snapshot(self) -> AppStateSnapshot:
        return AppStateSnapshot(
            clients=list(self.clients.values()),
            conversations=deepcopy(self.conversations),
            recommendations=deepcopy(self.recommendations),
            tasks=deepcopy(self.tasks),
        )

    def replace_conversation(self, client_id: str, conversation: list[ConversationEvent]) -> None:
        if client_id not in self.clients:
            raise ValueError(f"Unknown client: {client_id}")
        self.conversations[client_id] = conversation

    def update_client(self, client_id: str, **attributes) -> Client:
        client = self.clients.get(client_id)
        if client is None:
            raise ValueError(f"Unknown client: {client_id}")
        updated = client.model_copy(update=attributes)
        self.clients[client_id] = updated
        return updated

    def update_task_status(self, task_id: str, status: str) -> Task:
        for index, task in enumerate(self.tasks):
            if task.task_id == task_id:
                updated = task.model_copy(update={"status": status})
                self.tasks[index] = updated
                return updated
        raise ValueError(f"Unknown task: {task_id}")

    def update_policy(self, policy_id: str, **attributes):
        for index, policy in enumerate(self.policies):
            if policy.policy_id == policy_id:
                updated = policy.model_copy(update=attributes)
                self.policies[index] = updated
                return updated
        raise ValueError(f"Unknown policy: {policy_id}")


store = InMemoryStateStore()
