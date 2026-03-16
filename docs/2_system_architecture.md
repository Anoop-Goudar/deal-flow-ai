# DealFlow AI - System Architecture

## High-Level Architecture
Client / Agent UI
-> Backend API
-> Conversation Service
-> AI Pipeline
   - Requirement Detection (LLM)
   - Policy Retrieval (RAG)
   - Eligibility Engine
   - Recommendation Generator
-> Task Router
-> State Store
-> Dashboard UI

## Components
### 1. Conversation Service
Manages client-agent conversation threads, message ingestion, and retrieval of thread history by client.

### 2. AI Pipeline
Processes conversations and produces structured outputs such as product candidates, eligibility status, recommendations, and tasks.

### 3. Policy Retrieval System (RAG)
Retrieves relevant product policy documents from a vector store based on the detected need or candidate product.

### 4. Eligibility Engine
Applies rule-based checks against client profile and policy constraints.

### 5. Task Router
Maps recommendation outcomes to the correct operational actor or specialist.

### 6. State Manager
Stores the latest recommendation, generated tasks, and demo application state.

## Suggested Tech Stack
- Backend: Python with FastAPI
- LLM Provider: OpenAI or Claude
- Vector Database: Chroma
- UI: Streamlit
- State Store: In-memory dictionary for demo, with a clear seam for future database replacement

## Deployment Assumptions
- The initial implementation is a local demo or internal prototype.
- External dependencies should be isolated behind service interfaces to simplify testing and provider swaps.
- Mock data should be available so the system can run without live banking integrations.
