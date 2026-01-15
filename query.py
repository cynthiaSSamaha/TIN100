import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=45.0,  # prevents hanging
)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

query = "Hvordan søker permisjon?"

# -------------------------
# FIX 1: Proper system prompt (single coherent string)
# -------------------------
SYSTEM_PROMPT = (
    "Du er en profesjonell studieveileder. "
    "Du skal utelukkende basere svarene dine på informasjonen som er hentet fra databasen. "
    "Svarene skal være sammenhengende, velstrukturerte og gjennomtenkte, "
    "med tydelig faglig presisjon. "
    "Unngå spekulasjon og antagelser. "
    "Dersom databasen ikke gir tilstrekkelig grunnlag for å besvare spørsmålet, "
    "skal du svare eksakt med: "
    "«Jeg har dessverre ikke tilgang på denne informasjonen.» "
    "Språket skal være formelt, klart og veiledende, "
    "og tilpasset studenter i høyere utdanning."
)

# -------------------------
# Embedding
# -------------------------
embedding = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=query
).data[0].embedding

# -------------------------
# Supabase retrieval
# -------------------------
result = supabase.rpc(
    "match_embeddings",
    {
        "query_embedding": embedding,
        "match_count": 5
    }
).execute()

# -------------------------
# FIX 2: Safe context building
# -------------------------
context = "\n".join(
    (row.get("text") or row.get("content") or "").strip()
    for row in (result.data or [])
    if (row.get("text") or row.get("content"))
)

# -------------------------
# Chat completion
# -------------------------
response = openai_client.response.create(
    model="gpt-5-mini",
    max_tokens=500,  # FIX 3: required to avoid empty output
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Context:\n{context}\n\n"
                f"Spørsmål:\n{query}"
            ),
        },
    ],
)

# -------------------------
# FIX 4: Safe answer handling
# -------------------------
answer = response.output_text.strip()

if not answer:
    answer = "Jeg har dessverre ikke tilgang på denne informasjonen."

print(answer)
