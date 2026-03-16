from __future__ import annotations

from models import Client, ConversationEvent, PipelineResult, SuggestedReply, Task


class ReplySuggestionService:
    def suggest(
        self,
        client: Client,
        conversation: list[ConversationEvent],
        pipeline_result: PipelineResult | None,
        tasks: list[Task],
    ) -> list[SuggestedReply]:
        latest_client_message = next(
            (event.message for event in reversed(conversation) if event.actor == "client"),
            "",
        )
        latest_context = self._client_context_intro(latest_client_message)
        latest_message_lower = latest_client_message.lower()

        if pipeline_result is None or not pipeline_result.recommendations:
            missing_profile_fields = self._missing_profile_fields(client)
            if not missing_profile_fields:
                return [
                    SuggestedReply(
                        title="Acknowledge Update",
                        message=(
                            f"{latest_context}I’ve noted the details you shared and will review the most suitable next step for "
                            f"{client.name}."
                        ),
                    )
                ]
            return [
                SuggestedReply(
                    title="Request Details",
                    message=(
                        f"{latest_context}To assess the best option for {client.name}, "
                        f"please confirm {self._join_fields(missing_profile_fields)}."
                    ),
                )
            ]

        recommendations = pipeline_result.recommendations
        eligible = [item for item in recommendations if item.eligibility == "Eligible"]
        incomplete = [item for item in recommendations if item.eligibility == "Eligibility incomplete"]
        not_eligible = [item for item in recommendations if item.eligibility == "Not eligible"]

        suggestions: list[SuggestedReply] = []

        if eligible:
            primary = eligible[0]
            suggestions.append(
                SuggestedReply(
                    title="Confirm Next Step",
                    message=(
                        f"{latest_context}Based on what you've shared, "
                        f"{primary.product} looks suitable at this stage. "
                        f"The next step would be to {self._sentence_case(primary.next_action)}."
                    ),
                )
            )
            suggestions.append(
                SuggestedReply(
                    title="Request Documents",
                    message=(
                        f"{latest_context}To move this forward, please share your latest financial statements and "
                        "any supporting documents relevant to the request so we can complete the review."
                    ),
                )
            )

        if incomplete:
            fields = ", ".join(incomplete[0].missing_fields).replace("_", " ")
            suggestions.append(
                SuggestedReply(
                    title="Collect Missing Info",
                    message=(
                        f"{latest_context}To continue the assessment, I still need a few missing details for "
                        f"{incomplete[0].product}: "
                        f"{fields}. Once you share those, I can refine the recommendation."
                    ),
                )
            )

        if not_eligible:
            products = self._join_products([item.product for item in not_eligible])
            if any(token in latest_message_lower for token in ["criteria", "criterion", "why", "eligible", "available"]):
                suggestions.append(
                    SuggestedReply(
                        title="Explain Criteria",
                        message=self._build_criteria_reply(
                            latest_context=latest_context,
                            client=client,
                            recommendations=not_eligible,
                        ),
                    )
                )
            suggestions.append(
                SuggestedReply(
                    title="Explain Ineligibility",
                    message=(
                        f"{latest_context}Based on the current policy, {products} "
                        f"{'is' if len(not_eligible) == 1 else 'are'} not yet available for {client.name}. "
                        "I can walk you through the eligibility gap, discuss alternatives, and explain when a future review would make sense."
                    ),
                )
            )
            suggestions.append(
                SuggestedReply(
                    title="Offer Alternatives",
                    message=(
                        f"{latest_context}Although these facilities are not yet available, I can help review alternative options "
                        "that may be more suitable at this stage and outline what would strengthen eligibility later."
                    ),
                )
            )

        if tasks:
            pending = [task for task in tasks if task.status != "completed"]
            if pending:
                suggestions.append(
                    SuggestedReply(
                        title="Set Expectations",
                        message=(
                            f"{latest_context}I've noted the updated position and will coordinate the next steps. "
                            f"For now, the focus is to {self._sentence_case(pending[0].action)}."
                        ),
                    )
                )

        deduped: list[SuggestedReply] = []
        seen = set()
        for suggestion in suggestions:
            if suggestion.message in seen:
                continue
            seen.add(suggestion.message)
            deduped.append(suggestion)
        return deduped[:3]

    def _build_criteria_reply(
        self,
        latest_context: str,
        client: Client,
        recommendations,
    ) -> str:
        criteria_lines = []
        for recommendation in recommendations:
            criteria_lines.append(
                f"For {recommendation.product}, the current criteria are: {self._sentence_case(recommendation.policy_excerpt)}"
            )

        gap_line = ""
        if client.business_years is not None:
            gap_line = (
                f"At the moment, {client.name} is showing {client.business_years} years in operation, "
                "so the operating history is still below the current threshold."
            )

        pieces = [latest_context.rstrip()]
        pieces.append("Here is the current policy criteria.")
        pieces.extend(criteria_lines)
        if gap_line:
            pieces.append(gap_line)
        pieces.append("Once the business meets those requirements, we can revisit the application.")
        return " ".join(piece for piece in pieces if piece)

    def _missing_profile_fields(self, client: Client) -> list[str]:
        missing: list[str] = []
        if client.business_turnover is None:
            missing.append("your annual turnover")
        if client.business_years is None:
            missing.append("how many years the business has been operating")
        if client.collateral_available is None:
            missing.append("whether any collateral is available")
        return missing

    def _join_fields(self, fields: list[str]) -> str:
        if not fields:
            return "the remaining details"
        if len(fields) == 1:
            return fields[0]
        if len(fields) == 2:
            return f"{fields[0]} and {fields[1]}"
        return f"{', '.join(fields[:-1])}, and {fields[-1]}"

    def _client_context_intro(self, latest_client_message: str) -> str:
        if not latest_client_message:
            return ""

        lower_message = latest_client_message.lower()
        if any(token in lower_message for token in ["year", "turnover", "$", "million"]):
            return "Thank you for the clarification. "
        if any(token in lower_message for token in ["not available", "why", "eligible"]):
            return "I understand your concern. "
        if any(token in lower_message for token in ["export", "fleet", "equipment", "card"]):
            return "Thank you for the additional context. "
        return "Thank you for the update. "

    def _join_products(self, products: list[str]) -> str:
        if not products:
            return ""
        if len(products) == 1:
            return products[0]
        if len(products) == 2:
            return f"{products[0]} and {products[1]}"
        return f"{', '.join(products[:-1])}, and {products[-1]}"

    def _sentence_case(self, text: str) -> str:
        if not text:
            return text
        return text[0].lower() + text[1:]
