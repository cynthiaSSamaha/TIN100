

"use client";

import { useState } from "react";

type Message = {
  role: "user" | "bot";
  text: string;
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", text: "Hei 😄 Skriv noe så svarer jeg!" },
  ]);

  const [input, setInput] = useState("");

  function handleSend() {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", text: input };

    // Legg inn brukermeldingen
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Fake bot-svar (vi kobler til ekte AI senere)
    setTimeout(() => {
      const botMessage: Message = {
        role: "bot",
        text: "Dette er et test-svar ✅ (vi kobler ekte chatbot senere)",
      };
      setMessages((prev) => [...prev, botMessage]);
    }, 600);
  }

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        padding: "20px",
        gap: "12px",
      }}
    >
      {/* Header */}
      <div>
        <h1 style={{ margin: 0 }}>Chat</h1>
        <p style={{ marginTop: "6px", opacity: 0.8 }}>
          Fullskjerm chat-side ✅
        </p>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          border: "1px solid rgba(255,255,255,0.2)",
          borderRadius: "12px",
          padding: "12px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background:
                msg.role === "user"
                  ? "rgba(0, 150, 255, 0.25)"
                  : "rgba(255, 255, 255, 0.1)",
              padding: "10px 12px",
              borderRadius: "12px",
              maxWidth: "70%",
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input */}
      <div style={{ display: "flex", gap: "8px" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Skriv en melding..."
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          style={{
            flex: 1,
            padding: "12px",
            borderRadius: "10px",
            border: "1px solid rgba(255,255,255,0.2)",
            background: "transparent",
            color: "inherit",
            outline: "none",
          }}
        />
        <button
          onClick={handleSend}
          style={{
            padding: "12px 16px",
            borderRadius: "10px",
            border: "1px solid rgba(255,255,255,0.2)",
            background: "rgba(255,255,255,0.08)",
            cursor: "pointer",
            color: "inherit",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
