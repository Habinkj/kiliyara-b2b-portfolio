# Kiliyara — Autonomous B2B Technical Sales Agent

**Live demo:** https://kiliyara-b2b-agent.vercel.app/
**Walkthrough (5 min):** https://www.loom.com/share/14379e7ca1364f079d77161ba7fbcadd

---

## The Problem

B2B machinery buyers can't get fast technical answers. Specifications live buried
in 100-page PDF catalogs, and confirming a spec means waiting on a sales rep.
Kiliyara answers technical spec questions instantly from the source documents,
and when a question isn't technical, it switches into a lead-qualification mode
instead of wasting a database lookup.

## How It Works: The Classifier Cascade

Rather than sending every message through a single LLM prompt, Kiliyara classifies
intent *first*, using a multi-level cascade:

1. **Zero-cost heuristic (Level 1):** Scans for known technical keywords (e.g.
   "viscosity", "voltage"). On a match it routes straight to the vector DB — no
   tokens spent on classification.
2. **LLM evaluation (Level 2):** If the query is ambiguous, a lightweight LLM call
   classifies intent.
3. **Execution:** General questions bypass the DB entirely. Technical questions
   trigger a RAG pipeline (`k=3`) grounded in the Chroma vector store, so answers
   are tied to the source documents (this reduces hallucination — it does not
   eliminate it).

## Routing Impact (estimated — not yet benchmarked)

> These are reasoned estimates, labeled honestly as such. I have not load-tested
> at scale yet; measuring the real distribution is the next instrumentation step.

The general-query path skips retrieval entirely. Estimating payloads: a technical
query carries ~3 retrieved chunks plus the system prompt (order of ~850 tokens);
a general query carries just the system prompt and the question (order of ~45
tokens). That implies a large token reduction on bypassed queries — roughly an
order of magnitude, not a measured figure.

**Measured so far:** technical-route latency is ~5.4s end-to-end (from local logs).
General-route latency and the real bypass rate across a query distribution are not
yet measured.

## Architecture

```text
User → Next.js (Vercel)
  → FastAPI Gateway (Render)
    → LangGraph Router ── intent? ──┐
        ├─ TECHNICAL → RAG (k=3) → ChromaDB
        └─ GENERAL  → Direct LLM Response
```

**Stack:**

- **Orchestration:** LangGraph state machine, async `ainvoke` execution
- **LLM / embeddings:** Gemini 2.5 Flash, gemini-embedding-001
- **Vector store:** ChromaDB (local persistence)
- **Backend:** FastAPI + Pydantic, served by Uvicorn on Render
- **Frontend:** Next.js / React on Vercel
- **PDF parsing:** PyMuPDF
- **Observability:** LangSmith for node-level tracing and token tracking

## Engineering Decisions Worth Calling Out

**1. Blocking the event loop (sync vs. async).**
Calling synchronous LangGraph `.invoke()` inside a FastAPI endpoint blocked the
ASGI event loop — under concurrent requests, one slow call would stall others.
I refactored the routing endpoint to `await app.ainvoke()`, keeping the loop
unblocked under concurrent load.

**2. Failing gracefully when the upstream LLM doesn't answer.**
External LLM APIs time out and rate-limit (429). Instead of letting an unhandled
exception crash the backend, `/api/chat` is wrapped in a try/except that logs the
trace server-side and returns a `503` JSON response matching the Pydantic schema.
The frontend catches it and renders a clean degraded-state UI rather than breaking.

## Known Limits & What I'd Change at Scale

- **Vector store:** ChromaDB local is fine for a single-catalog prototype. At ~10k
  docs or real concurrency I'd move to PostgreSQL + `pgvector` for tenant-isolated
  namespaces and horizontal scaling.
- **Cold starts:** Render's free tier cold-starts add a noticeable delay on the
  first request — fine for a demo, not production. I'd containerize with Docker and
  deploy to Cloud Run / ECS for elastic, low-latency scaling.
- **Intent routing:** The heuristic layer misroutes on queries that don't contain
  obvious keywords; a confidence threshold falling back to RAG would be safer.

## Run Locally

```bash
git clone https://github.com/Habinkj/kiliyara-b2b-agent.git
cd kiliyara-b2b-agent
pip install -r requirements.txt

# Create a .env file based on .env.example
# Requires: GEMINI_API_KEY, LANGCHAIN_API_KEY (for tracing)
uvicorn main:app --reload
```
