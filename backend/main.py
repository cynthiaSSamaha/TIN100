import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import OpenAI
from supabase import create_client

# -------------------------
# 1) Load environment vars
# -------------------------
load_dotenv()  # Reads .env so os.getenv(...) works

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Safety: fail early if something is missing
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in backend/.env")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in backend/.env")

# -------------------------
# 2) Create clients
# -------------------------
openai_client = OpenAI(api_key=OPENAI_API_KEY)  # OpenAI client (kept server-side)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # Supabase client (server-side)

# -------------------------
# 3) FastAPI app
# -------------------------
app = FastAPI()

# -------------------------
# 4) CORS (lets browser call backend)
# -------------------------
# If your frontend runs on localhost:3000, you must allow it here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL allowed to call backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# 5) Request / Response schema
# -------------------------
class ChatRequest(BaseModel):
    query: str  # The user's question (what they typed)

class ChatResponse(BaseModel):
    answer: str  # What we send back to the frontend


# -------------------------
# 6) System prompt (your rules)
# -------------------------
SYSTEM_PROMPT = (
    "Du er en profesjonell studieveileder for NMBU. "
    "Du skal utelukkende basere svarene dine på informasjonen som er hentet fra databasen (context). "
    "Svarene skal være sammenhengende, velstrukturerte og gjennomtenkte, med tydelig faglig presisjon. "
    "Unngå spekulasjon og antagelser. "
    "Dersom databasen ikke gir tilstrekkelig grunnlag for å besvare spørsmålet, "
    "skal du svare nøyaktig: «Jeg har dessverre ikke tilgang på denne informasjonen.» "
    "Språket skal være formelt, klart og veiledende."
)

FALLBACK = "Jeg har dessverre ikke tilgang på denne informasjonen."


# -------------------------
# 7) Main endpoint: POST /chat
# -------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    query = req.query.strip()

    if not query:
        return {"answer": FALLBACK}

    # -----------------------------------------
    # Step A: Make embedding for the user query
    # -----------------------------------------
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    # -------------------------------------------------------
    # Step B: Retrieve relevant context from Supabase (RAG)
    # -------------------------------------------------------
    # This assumes you have a Supabase RPC function called "match_embeddings"
    # that returns rows containing at least a "text" column.
    result = supabase.rpc(
        "match_embeddings",
        {
            "query_embedding": embedding,
            "match_count": 5
        }
    ).execute()

    rows = result.data or []
    context = "\n".join(row.get("text", "") for row in rows).strip()

    # If we found no context -> do NOT guess
    if not context:
        return {"answer": FALLBACK}

    # -----------------------------------------
    # Step C: Ask OpenAI using ONLY the context
    # -----------------------------------------
    response = openai_client.chat.completions.create(
        model="gpt-5-mini",
        #temperature=0,  # Lower hallucination risk
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nSpørsmål:\n{query}"}
        ]
    )

    answer = (response.choices[0].message.content or "").strip()

    # Extra safety: if model returns empty, fallback
    if not answer:
        answer = FALLBACK

    return {"answer": answer}
