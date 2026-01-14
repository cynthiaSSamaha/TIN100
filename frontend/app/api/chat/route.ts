import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const last = body?.messages?.[body.messages.length - 1];

    return NextResponse.json({
      reply: `Test API works ✅ You said: ${last?.content ?? "(nothing)"}`,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Server error", details: String(err?.message ?? err) },
      { status: 500 }
    );
  }
}

