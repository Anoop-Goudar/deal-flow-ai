# Deployment Guide

## Recommended Team Sharing Setup
Use Docker Compose to run the backend and frontend together.

The stack includes:
- FastAPI backend on port `8000`
- React frontend served by Nginx on port `3000`

The frontend proxies `/api` requests to the backend, so your team can use one app URL:
- `http://localhost:3000`

## Prerequisites
- Docker Desktop or Docker Engine
- A populated `.env` file at the repo root

## Start The App
```bash
docker compose up --build
```

## Team Access
If you run this on a shared VM, teammates can open:
- `http://<server-ip>:3000`

## Environment Notes
Important variables:
- `DEALFLOW_LLM_PROVIDER`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `DEALFLOW_EMBEDDING_PROVIDER`
- `OPENAI_EMBEDDING_MODEL`

For a no-key demo, use:
- `DEALFLOW_LLM_PROVIDER=mock`
- `DEALFLOW_EMBEDDING_PROVIDER=mock`

## Persistent RAG Cache
The vector cache is stored in:
- `data/vector_index/`

Docker Compose mounts that folder into the backend container so the index survives container restarts.

## Production Notes
- This setup is suitable for internal demos and team review.
- For production, add:
  - persistent app database
  - auth
  - secrets manager
  - TLS via reverse proxy or load balancer
  - background jobs for pipeline work
