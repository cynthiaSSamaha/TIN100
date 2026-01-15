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
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=45.0,   # prevents hanging forever
)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# 3) FastAPI app
# -------------------------
app = FastAPI()

# -------------------------
# 4) CORS
# -------------------------
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
# 5) Schemas
# -------------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str


# -------------------------
# 6) Prompts (FIXED)
# -------------------------
SYSTEM_PROMPT = (
    "Du er en profesjonell studieveileder for NMBU.\n\n"
    "Du skal KUN bruke informasjonen som finnes i Context.\n"
    "IKKE bruk annen kunnskap.\n\n"
    "Hvis Context ikke inneholder tilstrekkelig informasjon til å svare på spørsmålet, "
    "skal du SVARE EKSAKT MED:\n"
    "«Jeg har dessverre ikke tilgang på denne informasjonen.»\n\n"
    "IKKE gi tomt svar.\n"
    "IKKE si at du er usikker.\n"
    "Svar alltid med tekst."
)

FALLBACK = "Jeg har dessverre ikke tilgang på denne informasjonen."


# -------------------------
# Root (test)
# -------------------------
@app.get("/")
def root():
    return {"status": "ok", "hint": "POST /chat"}


# -------------------------
# Main endpoint
# -------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    print("=== CHAT START ===")
    print("Query:", repr(req.query))

    try:
        query = (req.query or "").strip()
        if not query:
            print("Empty query → fallback")
            return {"answer": FALLBACK}

        # -------------------------
        # A) Embedding
        # -------------------------
        print("Creating embedding...")
        embedding = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
        ).data[0].embedding
        print("Embedding OK")

        # -------------------------
        # B) Supabase retrieval
        # -------------------------
        print("Querying Supabase RPC...")
        try:
            result = supabase.rpc(
                "match_embeddings",
                {
                    "query_embedding": embedding,
                    "match_count": 5,
                },
            ).execute()
            rows = result.data or []
            print(f"RPC returned {len(rows)} rows")
        except Exception as e:
            print("RPC error:", e)
            rows = []

        # -------------------------
        # C) Build context
        # -------------------------
        context_chunks = []
        for row in rows:
            chunk = row.get("text") or row.get("content") or ""
            if chunk.strip():
                context_chunks.append(chunk.strip())

        context = "\n\n".join(context_chunks)

        if not context:
            print("No context found → fallback")
            return {"answer": FALLBACK}

        print(f"Context length: {len(context)} chars")

        print("Calling OpenAI chat...")
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            max_completion_tokens=3000,  
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nSpørsmål:\n{query}",
                },
            ],
        )

        raw_answer = response.choices[0].message.content
        print("RAW MODEL OUTPUT repr:", repr(raw_answer))

        answer = (raw_answer or "").strip()
        print("Chat completed")

        return {"answer": answer or FALLBACK}

    except Exception as e:
        print("Unhandled error:", e)
        return {"answer": FALLBACK}

    finally:
        print("=== CHAT END ===")
