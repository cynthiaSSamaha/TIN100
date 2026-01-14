"use client";

import { useEffect, useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "Velkommen. Still et spørsmål om emner, karakterer eller regelverk ved NMBU.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    const nextMessages: Msg[] = [...messages, { role: "user", content: text }];

    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });

      // Robust parsing so we don't crash on empty/non-JSON responses
      const raw = await res.text();
      let data: any = {};
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error(`API returned non-JSON: ${raw}`);
      }

      if (!res.ok) {
        throw new Error(data?.error || `API error (${res.status})`);
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply ?? "Tomt svar fra API." },
      ]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Det oppstod en feil ved henting av svar. Vennligst prøv igjen.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex flex-col bg-neutral-950 text-neutral-100">
      {/* Header */}
      <header className="border-b border-white/10 px-4 py-3">
        <div className="mx-auto w-full max-w-3xl">
          <h1 className="text-lg font-semibold">Studieveileder (NMBU)</h1>
          <p className="text-sm text-white/60">
            Spørsmål om emner, karakterer og regelverk. Ved manglende grunnlag
            returneres: «Jeg har dessverre ikke tilgang på denne informasjonen.»
          </p>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto w-full max-w-3xl flex flex-col gap-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={[
                "w-full flex",
                m.role === "user" ? "justify-end" : "justify-start",
              ].join(" ")}
            >
              <div
                className={[
                  "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
                  m.role === "user"
                    ? "bg-sky-500/20 border border-sky-400/20"
                    : "bg-white/10 border border-white/10",
                ].join(" ")}
              >
                {m.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="w-full flex justify-start">
              <div className="max-w-[85%] rounded-2xl px-4 py-3 text-sm bg-white/10 border border-white/10 text-white/70">
                Skriver…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="border-t border-white/10 px-4 py-3">
        <div className="mx-auto w-full max-w-3xl flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Skriv et spørsmål…"
            className="flex-1 rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-neutral-100 placeholder:text-white/40 outline-none focus:border-white/25 focus:bg-white/10"
          />
          <button
            onClick={send}
            disabled={loading}
            className="rounded-xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-semibold hover:bg-white/15 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      </footer>
    </div>
  );
}



