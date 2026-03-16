# DealFlow AI

DealFlow AI is a local prototype that analyzes client conversations, recommends banking products, evaluates eligibility, and routes follow-up tasks to the right specialist.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Use `DEALFLOW_LLM_PROVIDER=mock` for the default demo flow. To enable OpenAI-backed extraction and need detection, set:
- `DEALFLOW_LLM_PROVIDER=openai`
- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=gpt-4o-mini`
- `DEALFLOW_EMBEDDING_PROVIDER=openai`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`

## Run the API
```bash
uvicorn main:app --reload
```

## Run the React UI
```bash
cd frontend
npm install
npm run dev
```

## Deploy On Vercel
Recommended approach: deploy as two Vercel projects from the same repo.

1. Backend project from the repo root
2. Frontend project from `frontend/`

Detailed steps are in [`docs/vercel-deployment.md`](./docs/vercel-deployment.md).

## Included Modules
- FastAPI server in `main.py`
- Shared domain models in `models.py`
- In-memory state and seed data in `state.py` and `mock_data.py`
- Core services in `services/`
- React frontend in `frontend/`
- Product catalog and policy corpus in `data/`
- Demo mock payloads in `data/mock/`
- Vercel deployment guide in [`docs/vercel-deployment.md`](./docs/vercel-deployment.md)

## RAG Setup
- Policies are chunked into smaller text spans inside the backend.
- Embeddings are generated per chunk and cached in `data/vector_index/policy_chunks.json`.
- Retrieval uses cosine similarity plus light token overlap scoring.
- If OpenAI embeddings are unavailable, the app falls back to a deterministic local embedding so the demo still works.
