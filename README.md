# Kiliyara AI: Autonomous B2B Technical Routing Engine

**Live Demo:** https://kiliyara-b2b-agent.vercel.app/
**Tech Stack:** Next.js, FastAPI, LangGraph, Gemini 2.5 Flash, ChromaDB, LangSmith.

### The Problem
Industrial machinery buyers cannot get fast technical answers—critical specifications are buried inside 100-page PDF catalogs, making technical sales reps a constant bottleneck. Kiliyara AI solves this by intercepting queries, answering technical specification questions instantly via local semantic search, and dynamically bypassing the database for general chatter to save API compute.

---

### The Core Architectural Decision: The Classifier Cascade
Sending every user message through a standard Retrieval-Augmented Generation (RAG) pipeline burns API tokens and adds massive latency to simple queries (e.g., "Hello," "Thanks"). 

Instead of a monolithic prompt, I engineered a **Classifier Cascade** using LangGraph:
1. **Zero-Cost Heuristic:** The system first scans for known technical keywords (e.g., "viscosity", "voltage", "torque"). If matched, it routes to the vector database instantly (0 tokens burned).
2. **LLM Evaluation:** If ambiguous, a lightweight LLM prompt classifies the intent. 
3. **Execution:** General queries are routed to a low-latency chat node. Technical queries trigger a strict semantic search (`k=3`) against a local ChromaDB instance, effectively making hallucinations structurally impossible.

*By intercepting the payload before database execution, this architecture drops average cost and latency by [INSERT %] on non-technical queries.*

---

### The Hard Part: The Asphyxiation Bug & The Router Tax
**1. The Router Tax:** Using an LLM to route intent introduces a ~60-token overhead to complex queries. I accepted this minor tradeoff to completely eliminate the ~2,500 token hemorrhage that occurs when a user sends a simple greeting into a naive RAG system.
**2. ASGI Thread Blocking:** Initially, synchronous LangGraph invocations (`app.invoke()`) blocked the FastAPI event loop, meaning concurrent users would choke the server. I refactored the primary routing endpoint to utilize fully asynchronous execution (`await app.ainvoke()`), keeping the worker threads unblocked under load.

---

### What I Would Change at Scale (10,000+ Concurrent Users)
* **Vector Storage:** Local ChromaDB (`persist_directory`) is sufficient for a single-tenant prototype. For a multi-tenant B2B SaaS deployment, I would migrate to a managed vector store like Pinecone or standard PostgreSQL with `pgvector` to allow for tenant-isolated namespaces and horizontal scaling.
* **Cold Starts:** Hosting the FastAPI gateway on Render's free tier introduces unacceptable cold-start latency (up to 50s). In production, I would containerize the microservice via Docker and deploy it to AWS ECS or Google Cloud Run for elastic, low-latency scaling.
