from __future__ import annotations

import json
from pathlib import Path

from models import Client, ConversationEvent, PolicyDocument

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MOCK_DIR = DATA_DIR / "mock"
POLICIES_DIR = DATA_DIR / "policies"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def seed_clients() -> dict[str, Client]:
    payload = _load_json(MOCK_DIR / "clients.json")
    return {item["client_id"]: Client.model_validate(item) for item in payload}


def seed_conversations() -> dict[str, list[ConversationEvent]]:
    payload = _load_json(MOCK_DIR / "conversations.json")
    conversations: dict[str, list[ConversationEvent]] = {}
    for client_id, events in payload.items():
        conversations[client_id] = [ConversationEvent.model_validate(event) for event in events]
    return conversations


def seed_policies() -> list[PolicyDocument]:
    product_catalog = _load_json(DATA_DIR / "products.json")
    policies: list[PolicyDocument] = []
    for product in product_catalog:
        policy_path = POLICIES_DIR / product["policy_file"]
        with policy_path.open("r", encoding="utf-8") as file:
            policy_text = file.read().strip()

        policies.append(
            PolicyDocument(
                policy_id=product["policy_id"],
                product=product["product"],
                title=product["title"],
                category=product["category"],
                policy_text=policy_text,
                policy_file=product["policy_file"],
                min_business_years=product.get("min_business_years"),
                min_turnover=product.get("min_turnover"),
                required_collateral=product.get("required_collateral"),
                requires_import_export_activity=product.get("requires_import_export_activity"),
                assigned_agent=product["assigned_agent"],
                next_action=product["next_action"],
            )
        )
    return policies
