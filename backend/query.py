import os
import re
from typing import Optional, Dict, Tuple, List

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

# -------------------------
# Load env + clients
# -------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in backend/.env")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in backend/.env")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Prompts / safety
# -------------------------
FALLBACK = "Jeg har dessverre ikke tilgang på denne informasjonen."

SYSTEM_PROMPT = (
    "Du er en profesjonell studieveileder for NMBU.\n"
    "Du skal KUN bruke informasjonen i CONTEXT.\n"
    f"Hvis svaret ikke kan utledes direkte fra CONTEXT, svar nøyaktig: «{FALLBACK}»\n"
    "Svar formelt, presist og veiledende.\n"
    "Ikke inkluder informasjon fra andre universiteter/høgskoler.\n"
)

# =========================================================
# 1) Emnekoder: finn emnekoder i spørsmålet
# =========================================================
EMNEKODE_REGEX = re.compile(r"\b[A-ZÆØÅ]{2,4}\d{3,4}\b")

def extract_emnekoder(text: str) -> List[str]:
    """Returnerer unike emnekoder i teksten, f.eks. ['TIN100', 'MATH101']"""
    return list(set(EMNEKODE_REGEX.findall((text or "").upper())))


# =========================================================
# 2) Hent emne fra Supabase-tabell "emner" og lag en tekstblokk
# =========================================================
def fetch_emne_block(emnekode: str) -> Optional[str]:
    """
    Henter emnet fra tabellen 'emner' og lager en tekstblokk som kan puttes i CONTEXT.
    Returnerer None hvis emnet ikke finnes.
    """
    try:
        r = (
            supabase
            .table("emner")
            .select("*")
            .eq("emnekode", emnekode)
            .single()
            .execute()
            .data
        )
    except Exception as e:
        print("EMNE LOOKUP ERROR:", e)
        return None

    if not r:
        return None

    def safe(key: str) -> str:
        v = r.get(key)
        return "" if v is None else str(v)

    # Bygg en strukturert blokk
    return "\n".join([
        "[EMNE]",
        f"Emnekode: {safe('emnekode')}",
        f"Navn: {safe('navn')}",
        f"Studiepoeng: {safe('studiepoeng')}",
        f"Fakultet: {safe('fakultet')}",
        f"Semester: {safe('semester')}",
        f"Språk: {safe('språk')}",
        "",
        "[INNHOLD]",
        f"Dette lærer du: {safe('dette_lærer_du')}",
        f"Forkunnskaper: {safe('forkunnskaper')}",
        f"Læringsaktiviteter: {safe('læringsaktiviteter')}",
        "",
        "[VURDERING]",
        f"Vurderingsordning: {safe('vurderingsordning')}",
        f"Obligatoriske aktiviteter: {safe('obligatoriske_aktiviteter')}",
        "",
        "[ANNET]",
        f"Fortrinnsrett: {safe('fortrinnsrett')}",
        f"Merknader: {safe('merknader')}",
    ])


# =========================================================
# 3) RAG/Embeddings: match_embeddings -> tekst chunks
# =========================================================
def rag_context(question: str, match_count: int = 10) -> str:
    """
    Henter relevante tekst-biter fra embeddings-DB via RPC match_embeddings.
    Returnerer en streng (kan være tom).
    """
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding

    result = supabase.rpc(
        "match_embeddings",
        {"query_embedding": embedding, "match_count": match_count}
    ).execute()

    rows = result.data or []

    # Hvis din RPC returnerer en annen kolonne enn "text", bruk fallback:
    chunks: List[str] = []
    for r in rows:
        t = r.get("text") or r.get("content") or r.get("chunk") or ""
        if t:
            chunks.append(str(t))

    return "\n\n---\n\n".join(chunks).strip()


# =========================================================
# 4) Build context: kombiner emneblokk + embeddings
# =========================================================
def build_context(question: str) -> str:
    """
    Lager CONTEXT som LLM får.
    Strategi (enkelt, funker bra i starten):
      - Hvis emnekoder finnes: legg til emneblokker
      - Alltid: prøv embeddings-søk også (for regler/annet materiale)
    """
    blocks: List[str] = []

    # A) emneblokker (hvis emnekode finnes)
    emnekoder = extract_emnekoder(question)
    for kode in emnekoder:
        b = fetch_emne_block(kode)
        if b:
            blocks.append(b)

    # B) embeddings (regler/FAQ/karakterinfo som ligger som tekst-chunks)
    try:
        rag = rag_context(question, match_count=12)
        if rag:
            blocks.append("[DOKUMENTASJON]\n" + rag)
    except Exception as e:
        print("RAG ERROR:", e)

    # Samle alt
    return "\n\n====================\n\n".join(blocks).strip()


# =========================================================
# 5) Main function backend calls
# =========================================================
def answer_question(question: str) -> str:
    q = (question or "").strip()
    if not q:
        return FALLBACK

    context = build_context(q)

    # Ingen grunnlag => aldri gjett
    if not context:
        return FALLBACK

    user_msg = f"CONTEXT:\n{context}\n\nSPØRSMÅL:\n{q}"

    resp = openai_client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )

    ans = (resp.choices[0].message.content or "").strip()
    return ans if ans else FALLBACK

