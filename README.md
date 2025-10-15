# Housy IA Chatbot

## Overview
Conversational assistant that recommends Peruvian real-estate listings. It orchestrates AWS Bedrock LLMs through LangChain and LangGraph, combining semantic search, structured workflows, and geolocation validation to surface relevant properties.

## Core Stack
- **AWS Bedrock**: foundation model inference and embeddings.
- **LangChain / LangGraph**: conversation graph, tool routing, and memory handling.
- **OpenSearch**: vector + keyword retrieval for property inventory.
- **PostgreSQL & DynamoDB**: structured property data and chat session state.
- **FastAPI**: exposes chatbot, fallback recovery, and embedding APIs.

## Key Modules
- `app/api/`: REST endpoints (`chatbot_endpoint`, `chatbot_recovery`, `embed_endpoint`).
- `app/services/chatbot_langgraph.py`: LangGraph workflow (intent analysis → retrieval → response).
- `app/services/embeddings/`: Bedrock embedding client and OpenSearch search utilities.
- `app/services/geolocation/`: fuzzy + forward geocoding, coordinate verification.
- `app/services/stages/`: LangChain subchains for extraction, FAQs, user follow-ups, small talk.
- `app/models/`: Pydantic schemas for chat state, history, property leads, and embed requests.
- `app/core/`: configuration loading and AWS session factories.
- `IA/test-lab/`: notebooks for dataset generation, search evaluation, and scoring experiments.

## Conversation Flow
1. **Intake**: API receives user need → `PropertySearchParams` serialized.
2. **Graph Execution**:
   - Intent detection & slot filling.
   - Geolocation verification (RapidFuzz / OpenCage).
   - Retrieval via Bedrock embeddings + OpenSearch.
   - Response drafting with Bedrock LLM, grounded in retrieved context.
3. **Persistence**: Chat history stored (DynamoDB), feedback logged for evaluation.
4. **Recovery Path**: If graph fails, recovery endpoint replays last state and retries with safe defaults.

## Running Locally
1. Copy `.env.example` to `.env` and provide AWS credentials, database URLs, and OpenSearch endpoints.
2. Install dependencies: `pip install -r requirements.txt`.
3. Launch API: `uvicorn app.main:app --reload`.
4. Optional tooling:
   - `scripts/dataset_generation.py`: synthesize property fixtures.
   - `scripts/evaluate_search_engine.py`: measure recall@k across districts.

## Testing & Evaluation
- `tests/`: unit coverage for API, embeddings, geolocation.
- `IA/test-lab`: Jupyter workflows assessing coordinate quality, query construction, and search scores.
- Use `pytest` (configured via `pyproject.toml`) to validate changes.

## Maintenance Checklist
- Monitor Bedrock & OpenSearch quotas.
- Refresh embeddings when property inventory changes.
- Keep geocoding providers (RapidFuzz thresholds, OpenCage key) aligned with data quality KPIs.
- Update LangGraph nodes when conversation policies evolve.