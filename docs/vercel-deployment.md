# Vercel Deployment

## Recommended Setup
Deploy this repo as two Vercel projects from the same Git repository:

1. Backend project
   - Root Directory: `/`
   - Runtime: FastAPI on Vercel
2. Frontend project
   - Root Directory: `/frontend`
   - Framework Preset: Vite

This is the simplest and most reliable setup for this codebase.

## 1. Backend Project
Import the repository into Vercel and keep the backend project pointed at the repo root.

Important files:
- `app.py`
- `main.py`
- `requirements.txt`
- `.python-version`

### Backend Environment Variables
Set these in the Vercel dashboard:
- `DEALFLOW_LLM_PROVIDER`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `DEALFLOW_EMBEDDING_PROVIDER`
- `OPENAI_EMBEDDING_MODEL`
- `DEALFLOW_ALLOWED_ORIGINS`

Example:
```text
DEALFLOW_LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
DEALFLOW_EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DEALFLOW_ALLOWED_ORIGINS=https://your-frontend-project.vercel.app
```

For a demo-only fallback deployment:
```text
DEALFLOW_LLM_PROVIDER=mock
DEALFLOW_EMBEDDING_PROVIDER=mock
```

## 2. Frontend Project
Create a second Vercel project from the same repository.

Set:
- Root Directory: `frontend`

### Frontend Environment Variable
Set:
```text
VITE_API_BASE=https://your-backend-project.vercel.app
```

## 3. Deploy Order
1. Deploy backend first
2. Copy the backend Vercel URL
3. Add it as `VITE_API_BASE` in the frontend project
4. Deploy frontend

## 4. Team Sharing
Share the frontend URL with your team. The frontend will call the backend using the configured `VITE_API_BASE`.

## Notes
- Vercel preview deployments will create different URLs. If you want preview frontend deployments to call the backend, update `DEALFLOW_ALLOWED_ORIGINS` accordingly or use a broader origin regex strategy later.
- The app still uses in-memory application state, so data resets on cold starts or redeploys.
