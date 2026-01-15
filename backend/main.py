"""
main.py
-------
Dette er API-laget. Den gjør bare:

- Starter FastAPI
- Setter CORS (så frontend får lov å kalle backend)
- Har endpoint POST /chat
- Kaller query.answer_question() og returnerer JSON
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from query import answer_question # importerer "hjernen" fra query.py

app = FastAPI()

# Frontend kjører vanligvis på localhost:3000 (eller 3001 hos deg)
# Legg til begge hvis du bytter port ofte.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

@app.get("/")
def healthcheck():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Logger i terminal så du ser at den blir truffet
    print("CHAT ENDPOINT HIT:", req.query)

    # Kall logikken i query.py
    answer = answer_question(req.query)

    return {"answer": answer}
