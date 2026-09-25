# Rewatch (alt, reconstructed): "Every Jev Concept Explained for Claude Users"

Video not watched. YouTube is blocked from this container. Built from TypeSafe's official docs (which the video walks through), the TypeSafe skill repo, launch coverage and independent benchmarks.

**Tags:**
- `[SOURCE: url]` means the claim comes from that page.
- `[SOURCE: video description]` means the fact was supplied by the caller from the YouTube description.
- `[INFERRED from chapter title]` means I am guessing what the video says from its chapter name plus the docs.
- `[ESTIMATE]` means my own arithmetic on sourced pricing.

---

## 1) Title, creator, length; what Jev is; pricing; access

- **Video:** "Every Jev Concept Explained for Claude Users" by Simon Scrapes, about 37 min, https://www.youtube.com/watch?v=D-Z5HnLW_ho [SOURCE: video description]
- **Jev** is TypeSafe AI's first "System One model". You send a `state` (text or JSON) and typed questions, and it returns typed answers with probabilities. It does not generate text, write code or chat. [SOURCE: https://docs.typesafe.ai/introduction.md] [SOURCE: https://docs.typesafe.ai/introduction/coding-agents.md]
- **Launch and funding:** Launched on 2026-09-15, when TypeSafe came out of stealth with a $40M seed round led by DCVC. The founder, Diogo Almeida, is ex-OpenAI and a co-inventor of RLHF. [SOURCE: https://www.beri.net/article/typesafe-jev-typed-decision-model-calibration-decomposition-shadow-eval] [SOURCE: https://typesafe.ai/blog/introducing-system-one-models-and-jev]
- **Training:** Jev is trained with "RLCD" (Reinforcement Learning for Calibrated Decisions). The goal is that answers given 0.8 probability come true about 80% of the time. This holds across groups of predictions and is not a guarantee for any single answer. [SOURCE: https://docs.typesafe.ai/introduction/machine-learning-primer.md]
- **Pricing and limits** [SOURCE: https://docs.typesafe.ai/models.md]:
  - **Price (`jev-1.13.0`):** $0.042 per million input tokens, which is $42 per billion. Output tokens are free.
  - **Rate limits:** 250k tokens/s and 1,200 requests/min. TypeSafe says these are "adjusting dynamically".
  - **Context:** 64k tokens per request. The `state` plus the longest question must fit in 32k.
  - **Input:** text only. English works best.
  - **Customisation:** no fine-tuning. You customise through the state and the question wording.
- **Speed claims:**
  - Around 100 ms for most queries [SOURCE: https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md].
  - 70–500 ms end to end [SOURCE: https://typesafe.ai/blog/introducing-system-one-models-and-jev].
  - The headline "193.6x faster, 444.6x cheaper" comes from TypeSafe's own workflow evals. Those evals use GPT-6 Astra and Fable 5.1 answers as the reference, and TypeSafe itself calls the figures "the higher end of real world gains" [SOURCE: same blog].
  - The description's "40–1,000x cheaper" figure does not appear in the docs [SOURCE: video description].
- **How to get access:**
  - Sign up at https://console.typesafe.ai, which has the Playground, API Keys and Usage pages.
  - Signup history: waitlist-only at launch, opened to everyone on 2026-09-20, **new signups paused on 2026-09-22**, still paused as of 2026-09-24. Accounts created before the pause keep working. [SOURCE: https://flaviocopes.com/jev-api-key/]
  - A "$5 free credit" is reported by unofficial sites only. Flavio says the docs don't cover free credits. [SOURCE: https://jev-ai.live/get-access/] [SOURCE: https://flaviocopes.com/jev-api-key/]
  - **Alternative route: Vercel AI Gateway**, model `typesafe-ai/jev`, same price. It is called through `experimental_evaluate` in AI SDK 7, and zero data retention and no-training are per-request flags. [SOURCE: https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway]
  - Jev is also listed on Cloudflare AI. [SOURCE: https://developers.cloudflare.com/ai/models/typesafe/jev/]
- **Description claims checked:**
  - **"Browser agent filling Google Flights in seconds":** this is Browser Use's `jev-ultrafast`, which does Zürich→London on Google Flights in 7.1 s, down from 9.5 s. [SOURCE: https://raw.githubusercontent.com/browser-use/jev-ultrafast/main/README.md] [SOURCE: https://news.lavx.hu/article/jev-ultrafast-cuts-browser-agent-time-by-25-with-typesafe-action-space]
  - **"3M website sessions for ~$2":** I could not find a source. Treat it as unverified. The closest published figures are 1,018 papers classified for $0.08 and 98k listings in 10 minutes. [SOURCE: https://flaviocopes.com/jev/]

## 2) Core thesis (2 sentences)

Let Claude keep the work that needs writing and reasoning, and hand the narrow "gut-check" decisions (classify, score, yes/no, route) to Jev. Jev returns typed answers with calibrated probabilities for roughly 1/100th of the cost and time, and your code then branches on those answers. [INFERRED from chapter titles 0:46–5:16, backed by SOURCE: https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md]

Design each Jev step backwards from the action your system takes. Ask many small, independent questions in one call, then use confidence to decide whether to act, escalate or hand off to Claude or a human. [INFERRED from chapter titles 18:31, 25:36 and 33:10; SOURCE: https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md]

## 3) Tools, repos, APIs and skills

| Item | What it does | URL / install |
|---|---|---|
| **TypeSafe agent skill** (`typesafe-ai`, v0.5.7, MIT) | A single SKILL.md, with no MCP server and no scripts. It is guidance that sends the agent to the live docs (`docs.typesafe.ai/llms.txt`, and any page + `.md`), tells it to start from the desired behaviour, pick Choice/Noul/Score, fan questions out, and gate on confidence. [SOURCE: https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md] [SOURCE: https://github.com/typesafe-ai/skills/tree/main/skills/typesafe-ai] | Claude Code: `claude plugin marketplace add typesafe-ai/skills` then `claude plugin install typesafe@typesafe-ai`. Invoke with `/typesafe:typesafe-ai`. Other agents: `npx skills add typesafe-ai/skills --skill typesafe-ai`. Update: `claude plugin marketplace update typesafe-ai && claude plugin update typesafe@typesafe-ai`. [SOURCE: https://docs.typesafe.ai/agent-skill.md] |
| **HTTP API** | One endpoint, `POST https://api.typesafe.ai/v1/systemone`, with a Bearer key. `GET /v1/models` lists models. Errors: 401/422/429/529. Choice allows at most 255 options; Score allows 2–10 levels. [SOURCE: https://docs.typesafe.ai/api.md] | Key from https://console.typesafe.ai/keys |
| **Python SDK** | `TypeSafeClient().system_one(state=..., questions={...})` with `Choice`, `Score` and `Noul` classes. Reads `TYPESAFE_API_KEY`, defaults to `jev-latest`, and retries with backoff. [SOURCE: https://docs.typesafe.ai/introduction/quickstart.md] | `pip install typesafe-sdk` (Python ≥3.10) |
| **JS SDK** | `@typesafe-ai/sdk`, providing `TypeSafeClient`, `choice()`, `noul()` and `score()`. [SOURCE: https://docs.typesafe.ai/models.md] [SOURCE: https://docs.typesafe.ai/llms.txt] | npm `@typesafe-ai/sdk` |
| **Playground** | Paste a state, add questions and see the answers. Includes lessons per primitive. [SOURCE: https://docs.typesafe.ai/introduction/quickstart.md] [SOURCE: https://flaviocopes.com/jev/] | https://console.typesafe.ai/playground |
| **Model IDs** | `jev-latest` and `jev-preview` both currently point to `jev-1.13.0`. Pin the versioned ID if you have tuned thresholds. [SOURCE: https://docs.typesafe.ai/models.md] | — |
| **Smart-home demo** | A Vite/React SPA used as the video's finale. Source is "available at release". [SOURCE: https://docs.typesafe.ai/demos/smart-home.md] | Loom: https://www.loom.com/embed/18c4dbcf8db546dfb2d7f2ef018e78e4 |
| **jev-ultrafast** (Browser Use) | Browser agent. Jev picks the operation and target element; a small LLM types text only when needed. [SOURCE: https://raw.githubusercontent.com/browser-use/jev-ultrafast/main/README.md] | `git clone https://github.com/browser-use/jev-ultrafast && uv sync && uv run jev` |
| **Vercel AI SDK** | `experimental_evaluate({model:'typesafe-ai/jev', state, questions})`. Note that this path calls the yes/no type `boolean`, not `noul`. [SOURCE: https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway] | `pnpm add ai@latest` (≥7.0.105) |
| **Skool resources** | `skool.com/scrapesai` is the free "Agentic Foundations" community and `skool.com/scrapes` is the paid "Agentic Academy" at $57/mo on sale. The public pages show only sales copy. **Any Jev resources are gated behind joining**, and I did not join. [SOURCE: https://www.skool.com/scrapesai] [SOURCE: https://www.skool.com/scrapes] | — |

## 4) Concepts per chapter

**0:46 A judgement model / 3:31 Why it's special:** State plus typed questions go in. Every question is evaluated **in parallel and in isolation** in one pass, so there is no context bleed between questions. Output is constrained to your options, so it cannot produce a type error; the "zero hallucinations" claim is a *schema* guarantee, not a truth guarantee. [SOURCE: https://docs.typesafe.ai/primitives.md] [SOURCE: https://typesafe.ai/blog/introducing-system-one-models-and-jev] How the video framed this is [INFERRED from chapter title].

**5:16 It replaces one job Claude does:** The "prompt-and-parse" step, where an LLM is asked to "return JSON". [SOURCE: https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md] [SOURCE: https://docs.typesafe.ai/introduction/coding-agents.md] Jev is *not* a replacement for the model behind Claude Code. [SOURCE: https://docs.typesafe.ai/introduction/coding-agents.md]

**6:23 Yes/no as a probability (called "Noul"):**
- Returns `noul` from 0 to 1, the probability of yes. It has no separate confidence value.
- 0.5 means "unsure", not "medium amount". If you need a degree, use a Score.
- Measured examples for "wants a human?":
  - "Thanks, that fixed it!" scored 0.02.
  - "Are you a bot?" scored 0.40.
  - "I have asked three times now… talk to a real person?" scored 0.99.
- Thresholds depend on cost: raise the bar when a false yes is expensive, and lower it when a missed yes is expensive.

[SOURCE: https://docs.typesafe.ai/primitives/noul.md]

**7:29 Choice gives odds on every option:**
```json
"department": {"type":"choice","instructions":"Which team should handle this",
  "criteria":{"billing":"Payment or subscription issues","technical":"Bugs or integration problems","sales":"Pricing or account questions"}}
```
Response: `{"choice":"technical","confidence":0.78,"probabilities":{"technical":0.85,"sales":0.0,"billing":0.15}}`. Choice allows up to 255 options, and you should add `other` or `none` for inputs that don't fit. [SOURCE: https://docs.typesafe.ai/introduction/quickstart.md] [SOURCE: https://docs.typesafe.ai/primitives/choice.md]

**8:04 Confidence, the second number:**
- Confidence is derived from how peaked the probability distribution is. Only Choice and Score answers carry it.
- The docs describe three bands: act automatically, proceed with caution or confirmation, and do not act (route to a human).
- Thresholds should scale with risk. The worked example routes anything below 0.5 to a human, lets `check_balance` act freely, and requires more than 0.9 before `approve_transfer` runs automatically.

[SOURCE: https://docs.typesafe.ai/confidence.md]

**9:20 Score for ordered options:**
- Score takes 2–10 levels written as descriptions. It returns `score`, the probability-weighted level.
- Example: "Safari export crash" scored 1.43 with probabilities `{0:0, 1:0.57, 2:0.43}` and confidence 0.35.
- Describe situations, not degrees. Levels labelled only with numbers performed badly (0.55 at confidence 0.33 versus 0.0 at confidence 1.0).
- Keep one dimension per Score.

[SOURCE: https://docs.typesafe.ai/primitives/score.md]

**11:04 Which type, and all three in one request:**
- Choice is for an unordered set, Score for a described spectrum, Noul for a clean yes/no. If two types fit, prefer the one your code can act on directly.
- The full quickstart example, one call with three answers and 392 input tokens:
```json
{"state":"Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.",
 "model":"jev-latest",
 "questions":{
  "department":{"type":"choice","instructions":"Which team should handle this","criteria":{"billing":"...","technical":"...","sales":"..."}},
  "frustration":{"type":"score","instructions":"How frustrated the customer appears","criteria":["Calm, just stating facts","Frustrated but civil","Very angry, strong language"]},
  "is_urgent":{"type":"noul","instructions":"The message conveys urgency or time-sensitivity"}}}
```
- The response includes `frustration.score=1.0` (confidence 1.0), `is_urgent.noul=1.0` and `usage.input_tokens=392`.

[SOURCE: https://docs.typesafe.ai/primitives.md] [SOURCE: https://docs.typesafe.ai/introduction/quickstart.md]

**12:40 In front of Claude, the guard that reads everything first:**
- The docs show two "Jev first" layouts:
  - **Intent routing:** Jev classifies every message, then sends it to deterministic code, a specialist LLM or a human, so "the expensive resources only get invoked for the requests that actually need them". [SOURCE: https://docs.typesafe.ai/patterns/intent-routing.md]
  - **Guardrails:** one request per message, input *and* output, containing a Noul per hazard plus a harm Score, with thresholds for pass, review, block or route. [SOURCE: https://docs.typesafe.ai/cookbooks/llm_guardrails.md]
- Caveat: "State is data, and jev-1.13 does not treat it as hostile by default." Injected text can move answers. [SOURCE: https://docs.typesafe.ai/model-jaggedness/jev-1.13.md]
- How the video framed the "guard" is [INFERRED from chapter title].

**14:22 The skill is a rulebook, not a tool:** SKILL.md contains no tool code. It states "The live TypeSafe docs are the source of truth. Read them as part of the task," maps tasks to docs pages, and gives design rules. [SOURCE: https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md] The docs add a warning: "Agents aren't great at writing questions", so keep questions and thresholds in one file for human review. [SOURCE: https://docs.typesafe.ai/agent-skill.md]

**18:31 Start from the action, not from the data:** From SKILL.md: "Start from the behavior the user wants: what will the application show, select, change, or hand off? Work backward to the judgments it needs. Keep known rules, calculations, exact lookups, and execution in code." [SOURCE: https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md]

**23:52 State as named fields:**
- Prefer a JSON object so each part of the state has a name. Point questions at parts with backticked paths, for example ``"Does `ticket.messages[0].text` request a refund?"``.
- Question IDs are not sent to the model, so the full meaning must be in `instructions`.
- Send only the context the question needs, because irrelevant detail lowers accuracy.

[SOURCE: https://docs.typesafe.ai/concepts/state.md] [SOURCE: https://docs.typesafe.ai/primitives.md] [SOURCE: https://docs.typesafe.ai/model-jaggedness/jev-1.13.md]

**25:36 Extra questions are almost free:**
- "Asking a question you might not need is close to free."
- Batching 13 questions over one article was 12.2x cheaper and 10x faster than 13 separate calls, with identical answers, because the state is billed once.

[SOURCE: https://docs.typesafe.ai/primitives.md] [SOURCE: https://docs.typesafe.ai/cookbooks/parallel_questions.md]

**29:02 Checklist for finding your own Jev steps:** [INFERRED from chapter title; the items below are assembled from these sources: https://docs.typesafe.ai/introduction/coding-agents.md, https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md, https://docs.typesafe.ai/model-jaggedness/jev-1.13.md]
- Does code currently ask an LLM for JSON, a label, a score or a yes/no?
- Is the answer drawn from a fixed set of options you can write down?
- Could a knowledgeable person make the call in a few seconds?
- Is it high volume, or does it need to be fast?
- Does acting on a wrong answer have a cheap fallback, such as review, Claude or a human?
- Is the judgment semantic rather than maths, dates or counting? Keep those in code.
- Can you give it an "other" or "not stated" exit?

**32:13 Pattern 1, ask everything at once (speculative fan-out):**
- One request per ticket asks five questions: a category Choice, a `bug_severity` Score, a `has_reproducible_steps` Noul, a `refund_requested` Noul and a `frustration` Score.
- Code then ignores the answers that don't apply. For example: `if category=="bug_report" and bug_severity.score>1.5 and repro.noul>0.6: escalate`.

[SOURCE: https://docs.typesafe.ai/patterns/fan-out.md]

**33:10 Pattern 2, confidence-gated routing:**
- Voice banking example: anything with confidence below 0.6 goes to a human.
- `check_balance` acts at 0.6 or above.
- `approve_transfer` acts automatically only above 0.85, and asks the user to confirm between 0.6 and 0.85.

[SOURCE: https://docs.typesafe.ai/patterns/confidence-routing.md]

**34:05 Pattern 3, score the parts and weight them yourself (composite scoring):**
- Resume example: four Scores of five levels each, divided by 4 to normalise.
- Senior IC weights: 0.40 Python, 0.10 leadership, 0.40 design, 0.10 generalist.
- Engineering manager weights: 0.15 Python, 0.40 leadership, 0.20 design, 0.25 generalist.
- If priorities change, change the weights, not the prompt.

[SOURCE: https://docs.typesafe.ai/patterns/composite-scoring.md]

**35:07 Pattern 4, route to the best handler (intent routing):**
- An intent Choice (`order_status`, `product_question`, `return_exchange`, `complaint`) plus a complexity Score.
- Confidence below 0.5 goes to a human.
- `order_status` goes to deterministic code; product questions and returns go to specialist LLMs.
- Complaints go to a human if complexity is above 1 or complexity confidence is below 0.5, and to an LLM otherwise.

[SOURCE: https://docs.typesafe.ai/patterns/intent-routing.md]

**35:54 All four together, the smart-home demo:**
- Speculative questions such as "What action should be taken on the lights?" are asked before the code knows the request is about lights.
- A Noul detects compound requests, which an LLM then splits into single commands.
- General chat falls back to an LLM. The Jev call is fast enough that it "adds negligible latency".

[SOURCE: https://docs.typesafe.ai/demos/smart-home.md]

**The video's own 50-email triage demo** (four piles, 4 s, a fraction of a cent) [SOURCE: video description] fits the docs' ticket-triage fan-out example. The actual code shown is unknown. [INFERRED]

**Known weak spots (jev-1.13)** [SOURCE: https://docs.typesafe.ai/model-jaggedness/jev-1.13.md]:
- Reads instructions literally.
- Unreliable at maths and counting.
- Can't compare dates.
- Struggles with indirection and double negatives.
- Gets distracted by large states with irrelevant content.
- Can be steered by adversarial content.
- Confused when instructions and criteria contradict each other.
- A Noul and a Choice asking the same thing are *not* interchangeable.
- Cannot generate text.

**Independent evidence** [SOURCE: https://www.beri.net/article/typesafe-jev-typed-decision-model-calibration-decomposition-shadow-eval]:
- **Phishing benchmark:** asked one question "is this phishing?", Jev scored 62.6% against Claude Haiku 4.5's 81.3%. With five atomic questions plus a regression fitted on 1,000 labelled emails, Jev reached 95.0% against Haiku's 93.2%.
- **Cost on that benchmark:** $0.038 per 1,000 emails for Jev, against $0.462 (Haiku, single question) and $1.02 (Haiku, five questions).
- **Out-of-distribution calibration:** expected calibration error (ECE) of 0.107, with yes/no answers *under*confident and Choice/Score answers *over*confident.
- **Pre-registered study:** 95.9% zero-shot, but 0 of 30 out-of-scope messages were flagged, all at 0.99 confidence.
- **Their advice:** calibrate per question, always include a "none" option, pin the model version, and run Jev in shadow against labelled history first.

## 5) UI likely shown

- **Claude Code terminal:** plugin install commands and `/typesafe:typesafe-ai`. [SOURCE: https://docs.typesafe.ai/agent-skill.md] That the video shows this on screen is [INFERRED from description "installs the Typesafe skill"].
- **TypeSafe console:**
  - A "Meet Jev" page listing properties and limits. [SOURCE: https://flaviocopes.com/jev/]
  - A Playground with the state editor on the left, a question-type picker, and lessons on the right covering resume screening, support-chat audit and helpdesk routing. [SOURCE: https://flaviocopes.com/jev/]
  - Whether the video shows the console at all is [INFERRED].
- **Docs pages:** mermaid flow diagrams for each pattern, including branches such as "below 0.6 → support agent" and "approve_transfer >0.85 → approve". [SOURCE: https://docs.typesafe.ai/patterns/confidence-routing.md]
- **Smart-home React demo** (Loom video). [SOURCE: https://docs.typesafe.ai/demos/smart-home.md]
- **Triage demo output:** 50 emails sorted into four piles. [SOURCE: video description] Its layout is unknown.

## 6) The 5 most actionable takeaways for NQ OS

**How the cost estimates work.** $0.042 per million tokens is $0.000000042 per input token. Each request carries roughly 250–300 tokens of fixed overhead: the API example with a single short Noul was billed 296 input tokens. [SOURCE: https://docs.typesafe.ai/api.md] [SOURCE: https://docs.typesafe.ai/models.md]

1. **/inbox-triage: put Jev in front and send only reply-worthy mail to Claude (fan-out plus confidence gate).**
   - **State:** `{email:{from, subject, body_trimmed}, known_clients:[...]}`.
   - **Questions in one call:**
     - `workstream` Choice: NQ, FD, SE, personal, vendor, spam, other.
     - `action` Choice: needs_reply, fyi, schedule, invoice/payment, lead, unsubscribe, other.
     - `urgent` Noul.
     - `new_business_inquiry` Noul.
     - `frustration` Score.
     - Phishing split into atomic Nouls (asks for credentials, sender/domain mismatch, unexpected reward), following the docs' spam decomposition.
   - **Routing:** if `action` confidence is below 0.6, the email goes to Claude or a manual pile. Only `needs_reply` emails reach Claude for drafting.
   - **Cost:** about 1,200 tokens per email, so about $0.00005 each. That is about $0.0025 for 50 emails and about $0.15/month at 100 emails a day. [ESTIMATE]

2. **/lead-research: composite lead score.**
   - Claude still researches, fetches and writes.
   - Jev scores each finished profile on separate 4–5 level Scores: ICP industry fit, company maturity or size band, evidence of paid-ads activity, stated pain or intent, and decision-maker reachability. Add a `competitor_or_existing_client` Noul.
   - Weights live in code, with a different set per workstream (FD-style ads clients vs SE production buyers). The docs' use-case map lists exactly this ("Match … to an ideal customer profile. Score industry fit … purchase intent"). [SOURCE: https://docs.typesafe.ai/concepts/use-case-map.md]
   - **Cost:** about 2,500 tokens per lead, so about $0.0001 each or about $0.11 per 1,000 leads. [ESTIMATE]

3. **FD ad and creative QA gate, run before anything goes to the client or platform.**
   - **State:** `{ad_copy, headline, cta, landing_page_text, brand_rules, prohibited_claims}`.
   - **Questions:**
     - One Noul per rule: unsubstantiated claim, prohibited term, copy and landing page mismatch, CTA missing, off-brand tone.
     - A `creative_quality` Score.
   - **Routing:** block if any hard-rule Noul is at 0.7 or above, send to review between 0.4 and 0.7, otherwise pass.
   - **Caveats:**
     - Text only, so image or video creatives need captions, OCR or a Claude description first. [SOURCE: https://docs.typesafe.ai/models.md]
     - Keep budgets, CPA and ROAS maths in code. Jev is "not a calculator", so it should not do /perf-report number crunching. [SOURCE: https://docs.typesafe.ai/model-jaggedness/jev-1.13.md]
   - **Cost:** about 4,000 tokens per ad, so about $0.00017 each or about $0.08 for 500 variants. [ESTIMATE]

4. **NQ OS request router (intent routing across workstreams and skills).**
   - One Choice for `workstream` and one Choice for `skill`, listing every NQ OS skill with structured `what` / `not_for` / `examples` criteria plus `none`. A `needs_human` Noul sits alongside.
   - **Routing:**
     - High confidence: run the deterministic skill, or Claude with the right workstream context loaded.
     - Low confidence: ask the user.
   - This matches the docs' intent-routing pattern and the 182-skill "skill suggestion" cookbook, which ranks with a Choice and then uses Nouls to decide whether to suggest any skill at all. [SOURCE: https://docs.typesafe.ai/patterns/intent-routing.md] [SOURCE: https://docs.typesafe.ai/cookbooks/skill_suggestion.md]
   - **Cost:** about 1,000 tokens per request, so about $0.13/month at 100 requests a day. [ESTIMATE]

5. **Adoption steps: shadow-test first and keep the rulebook reviewable.**
   - Install the skill and run the docs' brainstorm prompt ("explore the project and find opportunities for using intelligent judgement…"). Keep every question and threshold in one file. [SOURCE: https://docs.typesafe.ai/agent-skill.md]
   - Before trusting Jev, replay about 500–1,000 past emails or leads that have the user's real decisions attached. Pin `jev-1.13.0`, give every Choice a `none/other` option, and set thresholds per question from a confidence-vs-accuracy plot. [SOURCE: https://www.beri.net/article/typesafe-jev-typed-decision-model-calibration-decomposition-shadow-eval] [SOURCE: https://docs.typesafe.ai/confidence.md]
   - An evaluation of this size costs cents. The full 5,721-call pre-registered study cost $0.176. [SOURCE: same beri.net]
   - **Blockers to check:**
     - TypeSafe signups are paused, so the fallback is Vercel AI Gateway. [SOURCE: https://flaviocopes.com/jev-api-key/]
     - Client email and ad data: zero data retention is contractual only for enterprise customers, and on Vercel it is a per-request flag. [SOURCE: https://docs.typesafe.ai/models.md] [SOURCE: https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway]
     - Prompt-injection exposure on inbound email. [SOURCE: https://docs.typesafe.ai/model-jaggedness/jev-1.13.md]
   - **Verdict:** Jev fits as a cheap pre-filter in front of Claude on high-volume, repetitive decisions (inbox, leads, ad QA, routing). It gives little benefit on low-volume, reasoning-heavy or number-heavy steps such as /perf-report analysis. At NQ OS volumes the saving is mostly **latency and fewer Claude calls**, not dollars, because every one of these runs costs under $1/month. [INFERRED]
