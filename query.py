import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

query = "Hvordan søker permisjon?"

SYSTEM_PROMPT = "Du er en profesjonell studieveileder. Du skal utelukkende basere svarene dine på informasjonen som er hentet fra databasen. Svarene skal være sammenhengende, velstrukturerte og gjennomtenkte, med tydelig faglig presisjon. Unngå spekulasjon og antagelser." \
"Dersom databasen ikke gir tilstrekkelig grunnlag for å besvare spørsmålet, skal du eksplisitt opplyse om dette. Språket skal være formelt, klart og veiledende, og tilpasset studenter i høyere utdanning."


embedding = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=query
).data[0].embedding

result = supabase.rpc(
    "match_embeddings",
    {
        "query_embedding": embedding,
        "match_count": 5
    }
).execute()

context = "\n".join(row["text"] for row in result.data)

response = openai_client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{query}"}
    ]
)

answer = response.choices[0].message.content
print(answer)