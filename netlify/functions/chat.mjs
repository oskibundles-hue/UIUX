// ALIENATED — "Operator" AI help endpoint (Netlify Function, v2).
//
// Security: the Claude API key lives ONLY in the ANTHROPIC_API_KEY
// environment variable (set in the Netlify dashboard), never in the
// client bundle. The browser calls this function; this function calls Claude.
//
// Model: Claude Haiku 4.5 — fast + low cost, ideal for grounded FAQ answers.

const MODEL = "claude-haiku-4-5";
const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";

const SYSTEM = `You are "Operator", the customer-help assistant for ALIENATED — an independent fashion label. Collection 001 is "Static". Brand line: "Sorry I was high. Leave a message."

SCOPE: Only help with ALIENATED — its products, orders, shipping, returns, sizing, care, payment, and brand. If a question is unrelated to ALIENATED, briefly say you can only help with ALIENATED and point them to hello@alienated.studio. Never invent prices, policies, dates, discount codes, or any fact not listed below. If you don't know, say so and give the email.

VOICE: short, calm, a little deadpan, lowercase-friendly. Plain text only — no markdown headings or bold. Keep replies under 90 words.

FACTS:
- Products (3 pieces; colorways Toxic Green / Venom Pink / Sterling): Dead Air — Full Set (hoodie + skirt) $410; Dial Tone Zip-Hoodie $230; Voicemail Stud Skirt $195.
- The drop: Collection 001 is a numbered run of 200 per style. Once a size sells through it's gone — no restocks, no second pressings. Every piece is 1 of 200 with its number on a woven tag. Join the waitlist on the home page to hear about 002.
- Materials: real antique-silver metal pyramid studs (nothing plastic), stitched appliqué graphics (not printed), heavyweight washed fabric, hardware applied by hand.
- Sizing: cropped, low-rise, close to the body; runs small — size up if between sizes (especially the skirt). Made in XS–XL. Designed on a 5'8" fit model in size S. Full size guide on each product page.
- Shipping: packed in 1–3 business days; tracked link emailed when it ships. US 2–4 business days after dispatch; international 5–10 business days (customs/duties are the buyer's responsibility). Worldwide express, fully tracked. Free shipping over $250.
- Returns/exchanges: unworn, within 14 days of delivery, tags + numbered woven tag attached. Size exchanges ship free. Refunds to original payment once received. Final-sale items are marked at checkout.
- Care: real metal + appliqué — treat like a collectible. Machine wash cold gentle or hand wash; wash darks separately the first few washes; hang or lay flat to dry, never tumble (it loosens the studs); cool iron inside out avoiding studs and print; no bleach.
- Payment: secure checkout in USD — VISA, Mastercard, AMEX, PayPal, Apple Pay, Klarna, Afterpay.
- Discount: 10% off your first order with email signup, code ALIEN10.
- Orders / contact: tracking link emailed on dispatch. Questions, changes, or returns -> hello@alienated.studio, reply within 1–2 business days. Also on Instagram and TikTok.`;

const json = (obj, status) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });

export default async (req) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return json({ error: "not_configured" }, 503); // client falls back to its FAQ matcher

  let body;
  try { body = await req.json(); } catch { return json({ error: "bad_request" }, 400); }

  // Sanitize: only user/assistant string turns, last 12, capped length.
  const messages = (Array.isArray(body.messages) ? body.messages : [])
    .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
    .slice(-12)
    .map((m) => ({ role: m.role, content: m.content.slice(0, 1000) }));

  if (!messages.length || messages[messages.length - 1].role !== "user") {
    return json({ error: "bad_request" }, 400);
  }

  try {
    const r = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({ model: MODEL, max_tokens: 400, system: SYSTEM, messages }),
    });

    if (!r.ok) {
      console.error("anthropic error", r.status, (await r.text()).slice(0, 500));
      return json({ error: "upstream" }, 502);
    }

    const data = await r.json();
    const reply = (data.content || [])
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("")
      .trim();

    return json({ reply }, 200);
  } catch (e) {
    console.error("function error", e);
    return json({ error: "server" }, 500);
  }
};
