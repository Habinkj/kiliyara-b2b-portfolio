# Kiliyara — Autonomous B2B Technical Sales Agent

**Live demo:** https://kiliyara-b2b-agent.vercel.app/
**Walkthrough (5 min):** https://kiliyara-b2b-agent.vercel.app/

---

## The Problem

B2B machinery buyers can't get fast technical answers. Specifications live buried in 100-page PDF catalogs, and getting a spec confirmed means waiting on a sales rep. Kiliyara answers technical spec questions instantly from the source documents, and when a question isn't technical, it switches into a lead-qualification mode instead of wasting a database lookup.

## How It Works: The Classifier Cascade

Rather than sending every message through a single LLM prompt, Kiliyara classifies intent *first* using a multi-level cascade:

1. **Zero-Cost Heuristic (Level 1):** Scans for known technical keywords (e.g., "viscosity", "voltage"). If matched, it routes to the vector DB instantly (0 tokens burned, <1ms latency).
2. **LLM Evaluation (Level 2):** If ambiguous, a lightweight LLM classifies the intent. 
3. **Execution:** General questions bypass the DB entirely. Technical questions trigger a RAG pipeline (`k=3`) grounded strictly in the Chroma vector store.

**The Impact:** [Measure this in LangSmith: across 20 test queries, __% bypassed the DB. Average response time went from __s to __s on bypassed queries, and token cost dropped ~__%.]

## Architecture

**The Data Flow:**
User → Next.js (Vercel)
  → FastAPI Gateway (Render)
    → LangGraph Router ── intent? ──┐
      ├─ TECHNICAL → RAG Cascade → ChromaDB
      └─ GENERAL → Direct LLM Response

**The Stack Breakdown:**
- **Orchestration:** LangGraph state machine, asynchronous `ainvoke` execution.
- **LLM / Embeddings:** Gemini 2.5 Flash, gemini-embedding-001.
- **Vector Store:** ChromaDB (local persistence).
- **Backend:** Python FastAPI + Pydantic, served by Uvicorn on Render.
- **Frontend:** Next.js / React on Vercel.
- **Observability:** LangSmith for node-level telemetry and token tracking.

## Engineering Decisions Worth Calling Out

**1. The Asphyxiation Bug (Sync vs. Async Execution)**
Initially, calling synchronous LangGraph `.invoke()` inside a FastAPI endpoint blocked the ASGI event loop, meaning concurrent users would choke the server. I refactored the primary routing endpoint to utilize fully asynchronous execution (`await app.ainvoke()`), keeping worker threads unblocked under high concurrent load.

**2. Failover Redundancy at the Edge**
External LLM APIs will inevitably timeout or rate-limit. Instead of letting an unhandled exception crash the backend, the `/api/chat` endpoint is wrapped in a strict `try/except` block that logs the stack trace to the server and returns a graceful `503 Service Unavailable` JSON response matching the Pydantic schema. The frontend catches this and renders a clean "High Latency" UI state.

## Known Limits & What I'd Change at Scale

- **Vector Store:** ChromaDB local is fine for a single catalog prototype. At ~10k docs or real concurrency, I would migrate to PostgreSQL with `pgvector` to allow for tenant-isolated namespaces and horizontal scaling.
- **Cold Starts:** Render's free tier cold-starts add ~50s on the first request. Acceptable for a portfolio demo, but in production, I would containerize the microservice via Docker and deploy it to AWS ECS or Google Cloud Run for elastic, low-latency scaling.

## Run Locally

```bash
git clone [https://github.com/Habinkj/kiliyara-b2b-agent.git](https://github.com/Habinkj/kiliyara-b2b-agent.git)
cd kiliyara-b2b-agent
pip install -r requirements.txt

# Create a .env file based on .env.example
# Requires: GEMINI_API_KEY, LANGCHAIN_API_KEY (for tracing)
uvicorn main:app --reload
