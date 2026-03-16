from __future__ import annotations

from models import Client, EligibilityStatus, PolicyDocument


class EligibilityEngine:
    def evaluate(self, client: Client, policy: PolicyDocument) -> tuple[EligibilityStatus, list[str]]:
        missing_fields: list[str] = []

        if client.type != "business":
            return "Eligibility incomplete", ["business_type"]

        if client.business_years is None or client.business_turnover is None:
            if client.business_years is None:
                missing_fields.append("business_years")
            if client.business_turnover is None:
                missing_fields.append("business_turnover")
            return "Eligibility incomplete", missing_fields

        if policy.min_business_years is not None and client.business_years < policy.min_business_years:
            return "Not eligible", missing_fields

        if policy.min_turnover is not None and client.business_turnover < policy.min_turnover:
            return "Not eligible", missing_fields

        if policy.required_collateral and client.collateral_available is False:
            return "Not eligible", missing_fields

        if policy.required_collateral and client.collateral_available is None:
            return "Eligibility incomplete", ["collateral_available"]

        if policy.requires_import_export_activity and client.import_export_activity is False:
            return "Not eligible", missing_fields

        if policy.requires_import_export_activity and client.import_export_activity is None:
            return "Eligibility incomplete", ["import_export_activity"]

        return "Eligible", missing_fields
