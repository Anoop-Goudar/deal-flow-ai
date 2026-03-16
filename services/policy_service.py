from __future__ import annotations

import json
import re

from mock_data import DATA_DIR, POLICIES_DIR
from models import PolicyDocument, UpdatePolicyRequest
from state import store


class PolicyService:
    def __init__(self, rag_service) -> None:
        self.rag_service = rag_service
        self.products_path = DATA_DIR / "products.json"

    def list_policies(self) -> list[PolicyDocument]:
        return sorted(store.policies, key=lambda policy: policy.product)

    def update_policy(self, policy_id: str, payload: UpdatePolicyRequest) -> tuple[PolicyDocument, bool]:
        normalized_payload = payload.model_copy(
            update={"policy_text": self._synchronize_policy_text(payload)}
        )
        updated_policy = store.update_policy(policy_id, **normalized_payload.model_dump())
        persisted = self._persist_policy(updated_policy) and self._persist_product_catalog(updated_policy)
        self.rag_service.rebuild_index()
        return updated_policy, persisted

    def _synchronize_policy_text(self, payload: UpdatePolicyRequest) -> str:
        text = payload.policy_text.strip()

        if payload.min_business_years is not None:
            text = self._replace_first(
                text,
                r"(at least|more than)\s+\d+(?:\.\d+)?\s+years?",
                f"at least {payload.min_business_years} year{'s' if payload.min_business_years != 1 else ''}",
            )
            text = self._replace_first(
                text,
                r"operated for\s+(?:more than\s+)?\d+(?:\.\d+)?\s+years?",
                f"operated for at least {payload.min_business_years} year{'s' if payload.min_business_years != 1 else ''}",
            )

        if payload.min_turnover is not None:
            formatted_turnover = f"{int(payload.min_turnover):,}"
            text = self._replace_first(
                text,
                r"turnover above\s+[0-9,]+",
                f"turnover above {formatted_turnover}",
            )
            text = self._replace_first(
                text,
                r"turnover above\s+\$?[0-9,]+",
                f"turnover above {formatted_turnover}",
            )
            text = self._replace_first(
                text,
                r"annual turnover above\s+[0-9,]+",
                f"annual turnover above {formatted_turnover}",
            )
            text = self._replace_first(
                text,
                r"annual turnover above\s+\$?[0-9,]+",
                f"annual turnover above {formatted_turnover}",
            )

        return text

    def _replace_first(self, text: str, pattern: str, replacement: str) -> str:
        return re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)

    def _persist_policy(self, policy: PolicyDocument) -> bool:
        if not policy.policy_file:
            return False
        try:
            policy_path = POLICIES_DIR / policy.policy_file
            policy_path.write_text(policy.policy_text.strip() + "\n", encoding="utf-8")
            return True
        except OSError:
            return False

    def _persist_product_catalog(self, updated_policy: PolicyDocument) -> bool:
        try:
            payload = json.loads(self.products_path.read_text(encoding="utf-8"))
        except OSError:
            return False

        updated = False
        for item in payload:
            if item["policy_id"] != updated_policy.policy_id:
                continue
            item.update(
                {
                    "title": updated_policy.title,
                    "category": updated_policy.category,
                    "min_business_years": updated_policy.min_business_years,
                    "min_turnover": updated_policy.min_turnover,
                    "required_collateral": updated_policy.required_collateral,
                    "requires_import_export_activity": updated_policy.requires_import_export_activity,
                    "assigned_agent": updated_policy.assigned_agent,
                    "next_action": updated_policy.next_action,
                }
            )
            updated = True
            break

        if not updated:
            return False

        try:
            self.products_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return True
        except OSError:
            return False
