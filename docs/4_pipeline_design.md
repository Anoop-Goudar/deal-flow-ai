# AI Pipeline Design

The pipeline is triggered when:
- A client sends a message
- An internal agent sends a message
- An admin manually runs analysis

## Step 1 - Requirement Detection
Input:
- Conversation thread

Output:
```json
{
  "summary": "Client wants to expand its vehicle fleet.",
  "product_candidates": ["Vehicle Loan"]
}
```

## Step 2 - Policy Retrieval
RAG retrieves policy documents relevant to the detected product or need.

Example:
- Query: `Vehicle Loan`
- Retrieved document: `Vehicle Loan Policy`

## Step 3 - Eligibility Evaluation
The rule-based engine checks client attributes against policy requirements.

Example rule:
- `business_years >= 2`

Possible outputs:
- Eligible
- Not eligible
- Eligibility incomplete

## Step 4 - Recommendation Generation
Combine:
- Conversation summary
- Retrieved policy context
- Eligibility result

Output:
```json
{
  "recommended_product": "Vehicle Loan",
  "assigned_agent": "loan_specialist",
  "next_action": "Schedule vehicle loan consultation"
}
```

## Step 5 - Task Generation
Example:
```json
{
  "task": "Schedule vehicle loan consultation",
  "assigned_to": "loan_specialist"
}
```

## Implementation Notes
- Each stage should emit structured data to make the pipeline testable.
- LLM outputs should be normalized into explicit schemas before downstream steps consume them.
- The pipeline should support both mock implementations and real provider-backed services.
