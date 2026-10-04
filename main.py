from fastapi import FastAPI

from schemas import ChatRequest, ChatResponse
from session import add_message, get_history, reset_session


app = FastAPI(
    title="Smart Entrepreneur Cabinet API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Backend is running"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    add_message(
        request.session_id,
        "user",
        request.message
    )

    answer = "Это тестовый ответ backend."

    add_message(
        request.session_id,
        "assistant",
        answer
    )

    return ChatResponse(
        answer=answer,
        sources=[]
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