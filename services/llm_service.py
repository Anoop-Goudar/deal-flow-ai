from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from config import settings
from models import ExtractedAttributes, NeedAnalysisResult

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional runtime dependency
    OpenAI = None


class LLMService:
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self._client = None
        if self.provider == "openai" and settings.openai_api_key and OpenAI is not None:
            self._client = OpenAI(api_key=settings.openai_api_key)

    def _json_completion(self, prompt: str) -> dict[str, Any] | None:
        if self._client is None:
            return None

        try:
            response = self._client.responses.create(
                model=settings.openai_model,
                input=prompt,
            )
            text = getattr(response, "output_text", "").strip()
        except Exception:
            return None
        if not text:
            return None
        return self._parse_json_payload(text)

    def analyze_conversation(self, conversation_text: str) -> NeedAnalysisResult:
        prompt = (
            "Analyze this banking conversation and respond with JSON only. "
            "Return an object with keys summary, financial_needs, confidence, raw_signals. "
            "Do not include markdown fences or explanatory text.\n\n"
            f"Conversation:\n{conversation_text}"
        )
        if self.provider == "openai":
            payload = self._json_completion(prompt)
            if payload is not None:
                normalized = self._normalize_need_analysis_payload(payload)
                if normalized is not None:
                    try:
                        return NeedAnalysisResult.model_validate(normalized)
                    except ValidationError:
                        pass
        return self._mock_analyze_conversation(conversation_text)

    def extract_attributes(self, conversation_text: str) -> ExtractedAttributes:
        prompt = (
            "Extract client financial attributes from this conversation and respond with JSON only. "
            "Return an object with keys "
            "business_turnover, business_years, annual_revenue, monthly_salary, collateral_available, "
            "import_export_activity, notes. Do not include markdown fences or explanatory text.\n\n"
            f"Conversation:\n{conversation_text}"
        )
        if self.provider == "openai":
            payload = self._json_completion(prompt)
            if payload is not None:
                normalized = self._normalize_attribute_payload(payload)
                if normalized is not None:
                    try:
                        extracted = ExtractedAttributes.model_validate(normalized)
                        return self._overlay_conversation_facts(extracted, conversation_text)
                    except ValidationError:
                        pass
        return self._overlay_conversation_facts(self._mock_extract_attributes(conversation_text), conversation_text)

    def _parse_json_payload(self, text: str) -> dict[str, Any] | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_match:
            try:
                return json.loads(fenced_match.group(1))
            except json.JSONDecodeError:
                pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None

    def _normalize_need_analysis_payload(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        summary = payload.get("summary")
        if not isinstance(summary, str):
            summary = self._stringify_value(summary) or "Conversation analyzed."

        confidence = payload.get("confidence", "medium")
        if not isinstance(confidence, str):
            confidence = "medium"
        confidence = confidence.lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "medium"

        financial_needs = payload.get("financial_needs")
        if not isinstance(financial_needs, list):
            financial_needs = self._coerce_string_list(financial_needs)
        financial_needs = self._map_products(financial_needs)
        if not financial_needs:
            return None

        raw_signals = payload.get("raw_signals")
        if not isinstance(raw_signals, list):
            raw_signals = self._coerce_string_list(raw_signals)

        return {
            "summary": summary,
            "financial_needs": financial_needs,
            "confidence": confidence,
            "raw_signals": raw_signals,
        }

    def _normalize_attribute_payload(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        normalized = {
            "business_turnover": self._coerce_number(payload.get("business_turnover")),
            "business_years": self._coerce_int(payload.get("business_years")),
            "annual_revenue": self._coerce_number(payload.get("annual_revenue")),
            "monthly_salary": self._coerce_number(payload.get("monthly_salary")),
            "collateral_available": self._coerce_bool(payload.get("collateral_available")),
            "import_export_activity": self._coerce_bool(payload.get("import_export_activity")),
            "notes": self._coerce_string_list(payload.get("notes")),
        }

        if all(value in (None, []) for value in normalized.values()):
            extracted = self._extract_attributes_from_nested(payload)
            normalized.update(extracted)
        return normalized

    def _extract_attributes_from_nested(self, payload: dict[str, Any]) -> dict[str, Any]:
        flattened = json.dumps(payload).lower()
        return {
            "business_turnover": self._coerce_number(payload.get("turnover"))
            or self._coerce_number(payload.get("amount"))
            or self._coerce_number(self._extract_number_from_text(flattened, r"turnover[^0-9]*([0-9]+(?:\.[0-9]+)?)")),
            "business_years": self._coerce_int(payload.get("years"))
            or self._coerce_int(self._extract_number_from_text(flattened, r"years[^0-9]*([0-9]+)")),
            "annual_revenue": self._coerce_number(payload.get("annual_revenue"))
            or self._coerce_number(payload.get("turnover")),
            "monthly_salary": self._coerce_number(payload.get("monthly_salary")),
            "collateral_available": self._coerce_bool(payload.get("collateral"))
            or self._coerce_bool(payload.get("collateral_available")),
            "import_export_activity": self._coerce_bool(payload.get("import_export_activity"))
            or ("export" in flattened or "import" in flattened),
            "notes": self._coerce_string_list(payload),
        }

    def _coerce_string_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, dict):
            items: list[str] = []
            for key, nested_value in value.items():
                if nested_value in (True, "true", "yes", "eligible"):
                    items.append(str(key))
                elif isinstance(nested_value, str) and nested_value.strip():
                    items.append(nested_value.strip())
            return items
        if isinstance(value, str):
            if "," in value:
                return [part.strip() for part in value.split(",") if part.strip()]
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        return []

    def _map_products(self, items: list[str]) -> list[str]:
        catalog = {
            "vehicle": "Vehicle Loan",
            "fleet": "Vehicle Loan",
            "vehicle loan": "Vehicle Loan",
            "equipment": "Equipment Loan",
            "machinery": "Equipment Loan",
            "equipment loan": "Equipment Loan",
            "card": "Business Credit Card",
            "credit card": "Business Credit Card",
            "business credit card": "Business Credit Card",
            "trade": "Trade Finance",
            "export": "Trade Finance",
            "import": "Trade Finance",
            "trade finance": "Trade Finance",
        }
        mapped: list[str] = []
        for item in items:
            lower_item = item.lower()
            product = next((name for key, name in catalog.items() if key in lower_item), None)
            if product and product not in mapped:
                mapped.append(product)
        return mapped

    def _coerce_number(self, value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            normalized = value.replace(",", "").lower()
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", normalized)
            if match:
                number = float(match.group(1))
                if any(token in normalized for token in ["crore", "crores", "cr", "crs"]):
                    number *= 10_000_000
                elif any(token in normalized for token in ["lakh", "lakhs", "lac", "lacs"]):
                    number *= 100_000
                elif "m" in normalized or "million" in normalized:
                    number *= 1_000_000
                return number
        return None

    def _coerce_int(self, value: Any) -> int | None:
        number = self._coerce_number(value)
        return int(number) if number is not None else None

    def _coerce_bool(self, value: Any) -> bool | None:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower().strip()
            if lowered in {"true", "yes", "available", "provided"}:
                return True
            if lowered in {"false", "no", "none", "not available"}:
                return False
        return None

    def _extract_number_from_text(self, text: str, pattern: str) -> str | None:
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _stringify_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return "; ".join(f"{key}: {nested}" for key, nested in value.items())
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return str(value)

    def _overlay_conversation_facts(
        self,
        extracted: ExtractedAttributes,
        conversation_text: str,
    ) -> ExtractedAttributes:
        lower_text = conversation_text.lower()
        updates: dict[str, Any] = {}

        turnover = self._extract_latest_amount(lower_text)
        if turnover is not None:
            updates["business_turnover"] = turnover
            updates["annual_revenue"] = turnover

        latest_years = self._extract_latest_years(lower_text)
        if latest_years is not None:
            updates["business_years"] = latest_years

        collateral = self._extract_collateral_signal(lower_text)
        if collateral is not None:
            updates["collateral_available"] = collateral

        import_export = self._extract_import_export_signal(lower_text)
        if import_export is not None:
            updates["import_export_activity"] = import_export

        notes = list(extracted.notes)
        if "fleet" in lower_text and "Client mentioned fleet expansion" not in notes:
            notes.append("Client mentioned fleet expansion")
        if any(word in lower_text for word in ["import", "export"]) and "Client mentioned export or import activity" not in notes:
            notes.append("Client mentioned export or import activity")
        updates["notes"] = notes

        return extracted.model_copy(update=updates)

    def _extract_latest_amount(self, text: str) -> float | None:
        matches = list(
            re.finditer(
                r"\$?\s*([0-9]+(?:\.[0-9]+)?)\s*(crore|crores|cr|crs|lakh|lakhs|lac|lacs|m|million)\b",
                text,
            )
        )
        if matches:
            value = float(matches[-1].group(1))
            unit = matches[-1].group(2)
            if unit in {"crore", "crores", "cr", "crs"}:
                return value * 10_000_000
            if unit in {"lakh", "lakhs", "lac", "lacs"}:
                return value * 100_000
            return value * 1_000_000

        raw_matches = list(
            re.finditer(
                r"(?:turnover|revenue|annual turnover|annual revenue)[^0-9$]{0,24}\$?\s*([0-9]+(?:\.[0-9]+)?)\b",
                text,
            )
        )
        if raw_matches:
            return float(raw_matches[-1].group(1))
        return None

    def _extract_latest_years(self, text: str) -> int | None:
        patterns = [
            r"(?:operated|operating|operation|in business|business for|been operating for|years in operation|working from|working for|running for)[^0-9]{0,24}([0-9]+(?:\.[0-9]+)?)\s*years?\b",
            r"([0-9]+(?:\.[0-9]+)?)\s*years?\b",
        ]
        matches = []
        for pattern in patterns:
            matches.extend(re.finditer(pattern, text))
        if matches:
            latest_match = max(matches, key=lambda match: match.end())
            return int(float(latest_match.group(1)))
        return None

    def _extract_collateral_signal(self, text: str) -> bool | None:
        if any(phrase in text for phrase in ["cannot provide collateral", "no collateral", "without collateral"]):
            return False
        if "collateral" in text:
            return True
        return None

    def _extract_import_export_signal(self, text: str) -> bool | None:
        if any(phrase in text for phrase in ["no export", "no imports", "no import", "domestic only"]):
            return False
        if any(word in text for word in ["import", "export"]):
            return True
        return None

    def _mock_analyze_conversation(self, conversation_text: str) -> NeedAnalysisResult:
        lower_text = conversation_text.lower()
        needs: list[str] = []
        raw_signals: list[str] = []

        product_signals = {
            "Vehicle Loan": ["truck", "fleet", "vehicle", "van", "expand our fleet"],
            "Business Credit Card": ["card", "travel", "spend", "purchase", "limit"],
            "Trade Finance": ["import", "export", "supplier", "trade", "europe"],
            "Equipment Loan": ["equipment", "machinery", "warehouse equipment"],
        }

        for product, keywords in product_signals.items():
            matched = [keyword for keyword in keywords if keyword in lower_text]
            if matched:
                needs.append(product)
                raw_signals.extend(matched)

        if not needs:
            needs.append("Business Credit Card")
            raw_signals.append("general business spending need")

        summary = " ".join(segment.strip() for segment in conversation_text.splitlines()[-2:])
        confidence = "high" if len(raw_signals) >= 2 else "medium"
        return NeedAnalysisResult(
            summary=summary[:280],
            financial_needs=needs,
            confidence=confidence,
            raw_signals=sorted(set(raw_signals)),
        )

    def _mock_extract_attributes(self, conversation_text: str) -> ExtractedAttributes:
        lower_text = conversation_text.lower()

        amount_matches = re.findall(
            r"\$?\s*([0-9]+(?:\.[0-9]+)?)\s*(crore|crores|cr|crs|lakh|lakhs|lac|lacs|m|million)\b",
            lower_text,
        )
        turnover = None
        if amount_matches:
            numeric_value = float(amount_matches[-1][0])
            unit = amount_matches[-1][1]
            if unit in {"crore", "crores", "cr", "crs"}:
                multiplier = 10_000_000
            elif unit in {"lakh", "lakhs", "lac", "lacs"}:
                multiplier = 100_000
            else:
                multiplier = 1_000_000
            turnover = numeric_value * multiplier

        years_matches = re.findall(r"([0-9]+)\s*(years|year)\b", lower_text)
        business_years = int(years_matches[-1][0]) if years_matches else None

        return ExtractedAttributes(
            business_turnover=turnover,
            annual_revenue=turnover,
            business_years=business_years,
            collateral_available=True if "collateral" in lower_text else None,
            import_export_activity=True if any(word in lower_text for word in ["import", "export"]) else None,
            notes=[
                note
                for note in [
                    "Client mentioned fleet expansion" if "fleet" in lower_text else None,
                    "Client mentioned export or import activity"
                    if any(word in lower_text for word in ["import", "export"])
                    else None,
                ]
                if note
            ],
        )
