# UI Specification

The application contains three pages.

## Client Portal
The client can:
- View messages
- Respond to requests
- Submit missing details

## Agent Dashboard
The agent can:
- View client conversations
- See AI recommendations
- View tasks
- Send messages

Suggested layout:
- Left: Client list
- Center: Conversation thread
- Right: AI insights

## Admin Page
Functions:
- Edit mock conversation JSON
- Run pipeline manually
- Reset demo state

## UI Notes
- The initial implementation should optimize for clarity over styling complexity.
- Streamlit pages should expose the end-to-end workflow for demo purposes.
- AI insights should clearly show product recommendation, eligibility status, rationale, and routing outcome.
