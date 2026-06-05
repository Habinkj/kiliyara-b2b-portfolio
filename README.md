# Kiliyara B2B Agent | Autonomous LangGraph Routing System

**Live Demo:** https://kiliyara-b2b-agent.vercel.app/

## Architecture Overview
This is a fully decoupled, full-stack AI application designed to autonomously handle technical B2B sales inquiries. Instead of a basic single-prompt chatbot, this system utilizes a **LangGraph State Machine** to dynamically route user intents, optimizing API costs and eliminating AI hallucinations.

If a user asks for engineering specifications, the router triggers a Retrieval-Augmented Generation (RAG) pipeline querying a local Chroma vector database. If the user asks a general question, the system bypasses the database entirely and acts as an automated lead-qualification representative.

## The Tech Stack
* **Orchestration:** LangGraph, LangChain Core
* **LLM & Embeddings:** Google Gemini 2.5 Flash, Gemini-Embedding-001
* **Vector Database:** ChromaDB 
* **Backend:** Python FastAPI, Pydantic, Uvicorn (Deployed on Render)
* **Frontend:** React / Next.js (Deployed on Vercel)
* **Document Parsing:** PyMuPDF (Optimized for heavily compressed technical manuals)

## Core Engineering Features
1. **Dynamic Intent Routing:** Computes intent prior to execution to determine if a heavy database query is mathematically necessary.
2. **Semantic PDF Slicing:** Extracts and chunks enterprise machinery catalogs using LangChain’s `RecursiveCharacterTextSplitter` with strict overlap protocols to prevent cross-product data contamination.
3. **Decoupled API Gateway:** Fast-response Python endpoint fortified with strict CORS middleware and JSON schema validation to seamlessly connect with the strict Next.js frontend.
4. **State Management:** Utilizes LangGraph's `TypedDict` to pass context, intent, and historical data cleanly between distinct operational nodes.

## Local Installation
```bash
# 1. Clone the repository
git clone [https://github.com/](https://github.com/)[Your-Username]/kiliyara-b2b-agent.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Boot the FastAPI Server
uvicorn main:app --reload
