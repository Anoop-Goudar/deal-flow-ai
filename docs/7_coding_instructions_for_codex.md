# Coding Instructions For Codex

You are implementing DealFlow AI.

Follow the architecture and requirements defined in the `docs/` directory.

## Required Stack
- Python backend
- FastAPI API server
- Streamlit UI
- Chroma vector database
- OpenAI or Claude for LLM calls

## Expected Modules
```text
services/
    conversation_service.py
    pipeline.py
    rag_service.py
    eligibility_engine.py
    task_router.py

ui/
    client_portal.py
    agent_dashboard.py
    admin_page.py
```

## Implementation Guidance
- Keep external providers behind service interfaces so the app can run with mock implementations during development.
- Prefer strongly typed request and response models where possible.
- Build the project in a way that supports local demo execution with minimal setup.
- Use the documents in this folder as the source of truth for product scope, data shapes, pipeline stages, API contracts, and UI behavior.
