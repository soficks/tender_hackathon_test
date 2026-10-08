from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import ChatRequest, ChatResponse
from session import (
    add_message,
    get_history,
    reset_session
)
from rag.service import search_knowledge
from llm.client import generate_answer


app = FastAPI(
    title="Smart Entrepreneur Cabinet API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Backend is running"
    }


@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    add_message(
        request.session_id,
        "user",
        request.message
    )

    context = search_knowledge(
        request.message,
        top_k=3
    )

    answer = generate_answer(
        request.message,
        context
    )

    add_message(
        request.session_id,
        "assistant",
        answer
    )

    sources = [
        (
            f"{item['source']['source_doc']}, "
            f"стр. {item['source']['page']}"
        )
        for item in context
    ]

    return ChatResponse(
        answer=answer,
        sources=sources
    )


@app.get("/history/{session_id}")
def history(session_id: str):

    return {
        "messages": get_history(session_id)
    }


@app.delete("/reset/{session_id}")
def reset(session_id: str):

    reset_session(session_id)

    return {
        "status": "ok"
    }