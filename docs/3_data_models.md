# Data Models

## Client
```json
{
  "client_id": "C101",
  "name": "Orion Logistics",
  "type": "business",
  "business_turnover": 8000000,
  "business_years": 5
}
```

## Conversation Event
```json
{
  "timestamp": "2026-03-18T10:00:00Z",
  "actor": "client",
  "message": "We want to expand our truck fleet."
}
```

## Task
```json
{
  "task_id": "T101",
  "client_id": "C101",
  "assigned_to": "loan_specialist",
  "action": "Schedule vehicle loan consultation",
  "status": "pending"
}
```

## Recommendation
```json
{
  "client_id": "C101",
  "product": "Vehicle Loan",
  "eligibility": "Eligible",
  "assigned_agent": "loan_specialist"
}
```

## Policy Document
```json
{
  "product": "Vehicle Loan",
  "policy_text": "Business must operate more than 2 years and meet minimum turnover thresholds."
}
```

## Modeling Notes
- `client_id` is the primary identifier tying conversations, recommendations, and tasks together.
- `actor` values should be normalized to application roles such as `client`, `relationship_manager`, or specialist roles.
- `status` should begin with a simple lifecycle such as `pending`, `in_progress`, and `completed`.
- Timestamp values should use ISO 8601 formatting.
