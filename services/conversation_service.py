from __future__ import annotations

from models import AddMessageRequest, ConversationEvent
from state import store


class ConversationService:
    def list_clients(self):
        return list(store.clients.values())

    def get_client(self, client_id: str):
        client = store.clients.get(client_id)
        if client is None:
            raise ValueError(f"Unknown client: {client_id}")
        return client

    def get_conversation(self, client_id: str) -> list[ConversationEvent]:
        self.get_client(client_id)
        return list(store.conversations.get(client_id, []))

    def add_message(self, request: AddMessageRequest) -> ConversationEvent:
        self.get_client(request.client_id)
        event = ConversationEvent(actor=request.actor, message=request.message)
        store.conversations.setdefault(request.client_id, []).append(event)
        return event
