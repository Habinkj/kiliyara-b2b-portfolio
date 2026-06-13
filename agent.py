import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langgraph.graph import StateGraph, END

# Initialize Environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("CRITICAL: GEMINI_API_KEY not found in environment variables.")

# Initialize ChromaDB Vector Store
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vector_db.as_retriever(search_kwargs={"k": 3})

# Initialize Primary LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Define LangGraph State Schema
class AgentState(TypedDict):
    user_message: str
    intent: str
    technical_context: str
    final_answer: str

# Node: Intent Classification Strategy
def route_intent(state: AgentState):
    message = state["user_message"]
    prompt = f"""You are the Kiliyara AI routing agent. 
    Analyze the user's message. Output 'TECHNICAL' if they are asking about machine specifications, features, or technical operations. Output 'GENERAL' for non-technical queries or greetings.
    User Message: {message}"""
    
    response = llm.invoke(prompt)
    return {"intent": response.content.strip().upper()}

# Node: RAG Pipeline Execution
def retrieve_specs(state: AgentState):
    message = state["user_message"]
    docs = retriever.invoke(message)
    context = "\n\n".join([doc.page_content for doc in docs])
    return {"technical_context": context}

# Node: Direct LLM Bypass
def general_chat(state: AgentState):
    return {"technical_context": "No technical context required."}

# Node: Final Payload Generation
def generate_answer(state: AgentState):
    intent = state["intent"]
    context = state.get("technical_context", "")
    message = state["user_message"]
    
    if intent == "TECHNICAL":
        prompt = f"""You are Kiliyara AI, a B2B technical sales agent. 
        Answer the user's question using ONLY the following context retrieved from our catalog. 
        If the context does not contain the answer, state that you need to escalate to the engineering team. Do not guess.
        
        Context: {context}
        Question: {message}"""
    else:
        prompt = f"""You are Kiliyara AI, a professional enterprise assistant. 
        Respond politely and concisely to this message: {message}"""
        
    response = llm.invoke(prompt)
    return {"final_answer": response.content}

# Edge: Conditional Routing Logic
def route_to_next(state: AgentState):
    if state["intent"] == "TECHNICAL":
        return "retrieve_specs"
    return "general_chat"

# Compile LangGraph State Machine
workflow = StateGraph(AgentState)

workflow.add_node("route_intent", route_intent)
workflow.add_node("retrieve_specs", retrieve_specs)
workflow.add_node("general_chat", general_chat)
workflow.add_node("generate_answer", generate_answer)

workflow.set_entry_point("route_intent")
workflow.add_conditional_edges("route_intent", route_to_next)

workflow.add_edge("retrieve_specs", "generate_answer")
workflow.add_edge("general_chat", "generate_answer")
workflow.add_edge("generate_answer", END)

# Export the compiled graph
app = workflow.compile()