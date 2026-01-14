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
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in backend/.env")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in backend/.env")

# -------------------------
# 2) Create clients
# -------------------------
openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# 3) FastAPI app
# -------------------------
app = FastAPI()

# -------------------------
# 4) CORS (lets browser call backend)
# -------------------------
# If your frontend uses another port (3001, 3002), add it here too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# 5) Request / Response schema
# -------------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str


# -------------------------
# 6) System prompt (your rules)
# -------------------------
SYSTEM_PROMPT = (
    "Du er en profesjonell studieveileder for NMBU. "
    "Du skal utelukkende basere svarene dine på informasjonen som er hentet fra databasen (context). "
    "Ikke bruk kunnskap fra andre universiteter eller høgskoler i Norge. "
    "Svarene skal være formelle, klare og veiledende. "
    "Unngå spekulasjon og antagelser. "
    "Hvis databasen ikke gir tilstrekkelig grunnlag for å svare, skal du svare nøyaktig: "
    "«Jeg har dessverre ikke tilgang på denne informasjonen.»"
)

FALLBACK = "Jeg har dessverre ikke tilgang på denne informasjonen."


# -------------------------
# Optional: root endpoint (nice for testing)
# -------------------------
@app.get("/")
def root():
    return {"status": "ok", "hint": "Open /docs or POST /chat"}


# -------------------------
# 7) Main endpoint: POST /chat
# -------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        query = (req.query or "").strip()
        if not query:
            return {"answer": FALLBACK}

        # -------------------------
        # Step A: Make embedding
        # -------------------------
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        ).data[0].embedding

        # -------------------------
        # Step B: Retrieve context from Supabase
        # -------------------------
        # If the RPC function is missing or fails, we do NOT crash.
        try:
            result = supabase.rpc(
                "match_embeddings",
                {"query_embedding": embedding, "match_count": 5}
            ).execute()
            rows = result.data or []
        except Exception:
            rows = []

        # IMPORTANT:
        # Your RPC must return a column called "text" for this to work.
        # If your column is named differently (e.g. "content"), change row.get("text") below.
        context = "\n".join((row.get("text") or "") for row in rows).strip()

        if not context:
            # No retrieved info => no guessing
            return {"answer": FALLBACK}

        # -------------------------
        # Step C: Ask OpenAI using ONLY the context
        # -------------------------
        # NOTE: gpt-5-mini does NOT allow temperature=0 here, so we omit temperature.
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nSpørsmål:\n{query}"}
            ],
        )

        answer = (response.choices[0].message.content or "").strip()
        return {"answer": answer or FALLBACK}

    except Exception:
        # Never crash the server in production — return safe fallback
        return {"answer": FALLBACK}

