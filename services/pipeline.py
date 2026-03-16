from __future__ import annotations

from models import ExtractedAttributes, PipelineResult, ProductRecommendation
from state import store


class PipelineService:
    def __init__(
        self,
        conversation_service,
        rag_service,
        eligibility_engine,
        task_router,
        llm_service,
    ) -> None:
        self.conversation_service = conversation_service
        self.rag_service = rag_service
        self.eligibility_engine = eligibility_engine
        self.task_router = task_router
        self.llm_service = llm_service
        self.signal_map = {
            "Vehicle Loan": ["truck", "fleet", "vehicle", "van"],
            "Business Credit Card": ["card", "travel", "spend", "purchase", "limit"],
            "Trade Finance": ["import", "export", "supplier", "trade", "europe"],
            "Equipment Loan": ["equipment", "machinery", "warehouse"],
        }

    def detect_client_needs_with_llm(self, client_id: str):
        conversation = self.conversation_service.get_conversation(client_id)
        llm_result = self.llm_service.analyze_conversation(self._conversation_text(conversation))
        stabilized = self._stabilize_detected_needs(client_id, llm_result.financial_needs, conversation)
        return llm_result.model_copy(update={"financial_needs": stabilized})

    def extract_client_attributes(self, client_id: str) -> ExtractedAttributes:
        conversation = self.conversation_service.get_conversation(client_id)
        return self.llm_service.extract_attributes(self._conversation_text(conversation))

    def run(self, client_id: str) -> PipelineResult:
        client = self.conversation_service.get_client(client_id)
        need_analysis = self.detect_client_needs_with_llm(client_id)
        extracted_attributes = self.extract_client_attributes(client_id)

        updated_client = self._merge_client_attributes(client_id, client, extracted_attributes)
        recommendations: list[ProductRecommendation] = []
        tasks = []

        for product in need_analysis.financial_needs:
            retrieval_matches = self.rag_service.retrieve(
                query=self._retrieval_query(product, need_analysis.summary, need_analysis.raw_signals),
                limit=3,
                product_hint=product,
            )
            top_match = retrieval_matches[0] if retrieval_matches else None
            policy = self.rag_service.get_policy_for_product(product) or (
                self.rag_service.get_policy_by_id(top_match.policy_id) if top_match else None
            )
            if policy is None:
                continue

            eligibility, missing_fields = self.eligibility_engine.evaluate(updated_client, policy)
            rationale = self._build_rationale(updated_client, policy, need_analysis.raw_signals)
            confidence_score = self._confidence_to_score(need_analysis.confidence, need_analysis.raw_signals)
            assigned_agent, next_action = self._decision_outcome(policy, eligibility, missing_fields)
            recommendation = ProductRecommendation(
                product=policy.product,
                eligibility=eligibility,
                assigned_agent=assigned_agent,
                rationale=rationale,
                next_action=next_action,
                confidence=confidence_score,
                policy_excerpt=self._policy_excerpt(policy, top_match),
                retrieved_chunk=top_match.text if top_match else None,
                retrieval_score=top_match.score if top_match else None,
                missing_fields=missing_fields,
            )
            recommendations.append(recommendation)
            task = self._ensure_task(client_id, recommendation)
            tasks.append(task)

        self._sync_stale_tasks(client_id, recommendations)

        result = PipelineResult(
            client_id=client_id,
            summary=need_analysis.summary,
            confidence=need_analysis.confidence,
            detected_needs=need_analysis.financial_needs,
            extracted_attributes=extracted_attributes,
            recommendations=recommendations,
            tasks=tasks,
        )
        store.recommendations[client_id] = result
        return result

    def _merge_client_attributes(self, client_id, client, extracted_attributes: ExtractedAttributes):
        updates = {}
        for field_name, value in extracted_attributes.model_dump().items():
            if value not in (None, [], ""):
                updates[field_name] = value
        if updates:
            return store.update_client(client_id, **updates)
        return client

    def _ensure_task(self, client_id, recommendation):
        existing_task = next(
            (
                task
                for task in store.tasks
                if task.client_id == client_id
                and task.product == recommendation.product
                and task.assigned_to == recommendation.assigned_agent
                and task.action == recommendation.next_action
                and task.status != "completed"
            ),
            None,
        )
        if existing_task is not None:
            return existing_task
        return self.task_router.create_task(client_id, recommendation)

    def _sync_stale_tasks(self, client_id, recommendations):
        desired_signatures = {
            (recommendation.product, recommendation.assigned_agent, recommendation.next_action)
            for recommendation in recommendations
        }
        refreshed_tasks = []
        for task in store.tasks:
            if task.client_id == client_id and task.status == "pending":
                signature = (task.product, task.assigned_to, task.action)
                if signature not in desired_signatures:
                    continue
            refreshed_tasks.append(task)
        store.tasks = refreshed_tasks

    def _conversation_text(self, conversation):
        return "\n".join(f"{event.actor}: {event.message}" for event in conversation)

    def _policy_excerpt(self, policy, top_match):
        evidence_parts = []
        if policy.min_business_years is not None:
            evidence_parts.append(f"Business must operate for more than {policy.min_business_years} years.")
        if policy.min_turnover is not None:
            evidence_parts.append(f"Annual turnover should exceed {int(policy.min_turnover):,}.")
        if policy.required_collateral:
            evidence_parts.append("Collateral or financed asset security is required.")
        if policy.requires_import_export_activity:
            evidence_parts.append("Import or export activity should be present.")
        if evidence_parts:
            return " ".join(evidence_parts)
        excerpt = policy.policy_text.split(".")
        return ". ".join(part.strip() for part in excerpt[:2] if part.strip()) + "."

    def _build_rationale(self, client, policy, raw_signals):
        reasons = [f"conversation signals: {', '.join(raw_signals[:3]) or policy.product}"]
        if client.business_years is not None:
            reasons.append(f"business operating for {client.business_years} years")
        if client.business_turnover is not None:
            reasons.append(f"turnover captured at {int(client.business_turnover):,}")
        if policy.requires_import_export_activity:
            reasons.append("policy expects import or export activity")
        return "; ".join(reasons)

    def _confidence_to_score(self, confidence, raw_signals):
        base = {"low": 0.45, "medium": 0.68, "high": 0.87}[confidence]
        return min(base + min(len(raw_signals), 3) * 0.02, 0.97)

    def _retrieval_query(self, product, summary, raw_signals):
        signals = ", ".join(raw_signals[:5])
        return f"{product}. Summary: {summary}. Signals: {signals}"

    def _stabilize_detected_needs(self, client_id, llm_needs, conversation):
        combined = self._conversation_text(conversation).lower()
        stable_needs = list(dict.fromkeys(llm_needs))

        for product, keywords in self.signal_map.items():
            if any(keyword in combined for keyword in keywords) and product not in stable_needs:
                stable_needs.append(product)

        existing = store.recommendations.get(client_id)
        if existing is not None:
            for recommendation in existing.recommendations:
                product = recommendation.product
                keywords = self.signal_map.get(product, [])
                if any(keyword in combined for keyword in keywords) and product not in stable_needs:
                    stable_needs.append(product)

        return stable_needs

    def _decision_outcome(self, policy, eligibility, missing_fields):
        if eligibility == "Eligible":
            return policy.assigned_agent, policy.next_action

        if eligibility == "Eligibility incomplete":
            field_text = ", ".join(field.replace("_", " ") for field in missing_fields) or "required client details"
            return (
                "relationship_manager",
                f"Collect missing information for {policy.product}: {field_text}",
            )

        return (
            "relationship_manager",
            f"Explain {policy.product} is currently not eligible and discuss alternatives or future review",
        )
