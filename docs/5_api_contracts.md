# API Contracts

## Add Message
`POST /messages`

Request:
```json
{
  "client_id": "C101",
  "actor": "client",
  "message": "Our turnover is $8M."
}
```

Response:
```json
{
  "status": "message_added"
}
```

## Run Pipeline
`POST /pipeline/run`

Request:
```json
{
  "client_id": "C101"
}
```

Response:
```json
{
  "recommendation": {
    "client_id": "C101",
    "product": "Vehicle Loan",
    "eligibility": "Eligible",
    "assigned_agent": "loan_specialist"
  },
  "tasks": [
    {
      "task_id": "T101",
      "client_id": "C101",
      "assigned_to": "loan_specialist",
      "action": "Schedule vehicle loan consultation",
      "status": "pending"
    }
  ]
}
```

## Get Client Conversation
`GET /clients/{client_id}/conversation`

Expected response:
- Array of conversation events for the client ordered by timestamp ascending

## Get Tasks
`GET /tasks`

Expected response:
- Array of tasks, optionally filtered in future versions by assignee, status, or client

## Contract Notes
- Initial responses can be lightweight and demo-friendly.
- FastAPI request and response models should align with the data shapes defined in `docs/3_data_models.md`.
