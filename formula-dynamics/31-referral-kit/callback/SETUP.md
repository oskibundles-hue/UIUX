# QR callback: setup, step by step

What this is: someone scans a QR code, fills in a short form on their phone, and about two
minutes later an AI voice assistant rings them. It says it is an AI calling for Omarie about
Formula Dynamics, checks the car and what it needs, then sets a time for the shop to call them
(or puts them through to the shop if that is switched on). Every lead and its consent go into
`leads.csv`, and you get the summary by email or text.

You do every step that involves an account, money or a phone. Claude has not signed up for
anything, bought a number, called anyone or put anything online.

---

## Step 0. Nate's approval (cleared)

Omarie, in chat on 25 Nov 2026: "nate approves everything i do". So Nate's yes is covered,
and no written yes is needed before the first call.

Two shop details are still worth filling in, because the server can't guess them:
1. Should calls be put through to the shop? If yes, which number and which hours
   (`FD_SHOP_NUMBER`, `FD_SHOP_HOURS`). If not, leave them empty: the assistant books a time.
2. Who at FD calls back the booked times. The summary goes to you, so you pass it on.

The assistant never mentions money, deals or offers, so the commission talk does not block it.

---

## Step 1. Pick a provider

Both place the call, run the AI voice and send the report back. The server supports both; you
only need one.

| | Vapi (the default) | Retell |
|---|---|---|
| How the assistant is set up | The server sends the whole assistant with every call, straight from `agent_prompt.md`. Nothing to paste. | You build the assistant once in Retell's dashboard and paste the prompt in. |
| Change the wording later | Edit `agent_prompt.md`, restart the server. | Edit it in Retell's dashboard too. |
| Cost | Check current pricing on vapi.ai. Calls are charged per minute, the phone number per month. | Check current pricing on retellai.com. Calls are charged per minute, the phone number per month. |

My pick: **Vapi**, because the prompt file stays the one place the wording lives.

Also check, on whichever site you pick, the price of the AI model and voice it uses (some are
included in the per-minute price and some are not).

---

## Step 2. Sign up (you do this)

Make an account on the provider's site. Add a payment method only when you are ready to test.
Copy your **API key** (Vapi: Dashboard, then API Keys, the private key. Retell: Settings, then
API Keys). Treat it like a password: never paste it into a chat, a file in the repo or a message.

---

## Step 3. Buy a phone number

In the provider's dashboard, buy a number with a **702** area code, so people see a local Las
Vegas number. Write down:

- Vapi: the number's **ID** (a long code on the number's page, not the number itself).
- Retell: the number itself, in the form +17025551234.

Tip: call your own phone from it once. If it shows as "Spam likely", the provider's site explains
how to register the number's caller name.

---

## Step 4. Paste the prompt

**Vapi:** nothing to paste. The server sends it with every call.

**Retell:** make a new agent and fill it in from `agent_prompt.md`:

1. Prompt: paste everything between `<!-- SYSTEM_PROMPT -->` and `<!-- /SYSTEM_PROMPT -->`.
2. Begin message: paste the first-message block. Set it so the agent speaks first.
3. Voicemail: turn on voicemail detection and paste the voicemail block as the message.
4. Max call length: 3 minutes.
5. Transfer (only if Nate said yes): add the "transfer call" tool to FD's number, warm transfer.
6. Post-call analysis: add three fields, `outcome`, `booked_time` and `notes`, with the
   descriptions from the table at the bottom of `agent_prompt.md`.
7. Webhook URL: `https://<your server address>/webhook/retell?token=<your WEBHOOK_TOKEN>`.
8. Copy the agent's ID.

---

## Step 5. Set the settings (environment variables)

The server reads every key and setting from environment variables, never from a file in the repo.
On a host, there is a "Environment" or "Variables" page for these. On your Mac, you set them in
the Terminal before starting the server.

| Name | What to put | Needed |
|---|---|---|
| `CALLBACK_PROVIDER` | `vapi` or `retell` | yes (default vapi) |
| `VAPI_API_KEY` | your Vapi private key | Vapi |
| `VAPI_PHONE_NUMBER_ID` | the number's ID from Step 3 | Vapi |
| `RETELL_API_KEY` | your Retell key | Retell |
| `RETELL_FROM_NUMBER` | the Retell number, +1702... | Retell |
| `RETELL_AGENT_ID` | the agent ID from Step 4 | Retell |
| `PUBLIC_BASE_URL` | the server's public https address (Step 6) | yes |
| `WEBHOOK_TOKEN` | a long random password you make up (30+ letters and numbers) | yes |
| `FD_SHOP_NUMBER` | FD's number as +1702..., only if Nate wants calls put through | no |
| `FD_SHOP_HOURS` | when to offer the transfer, e.g. `mon-fri 09:00-17:00; sat 10:00-14:00` | with the shop number |
| `CALL_WINDOW` | hours the assistant may call, default `09:00-20:00` Las Vegas time | no |
| `NOTIFY_EMAIL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` | where your summary emails go and the mail account that sends them | one of email or text |
| `NOTIFY_SMS_TO`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM` | for a text summary instead (needs a Twilio account; check current pricing on twilio.com) | one of email or text |
| `VAPI_MODEL`, `VAPI_VOICE_PROVIDER`, `VAPI_VOICE_ID` | optional: pick the AI model and voice; leave empty for Vapi's defaults | no |

Leads that arrive outside the calling window are called the next morning when it opens. The
server never calls before 8 AM or after 9 PM, whatever you set.

---

## Step 6. Run the server

The server needs Python 3.10 or newer and nothing else. On your Mac, use `uv` (it is already
installed).

**First, the safe test (no calls).** In the Claude app, open the Terminal tab, paste this and
press Return:

    cd ~/.local/vlogtools/UIUX/.claude/worktrees/fd-referral-kit-422c18/formula-dynamics/31-referral-kit/callback
    uv run --no-project --python 3.12 python test_callback.py

You should see a list of PASS lines ending in `ALL PASS`. It uses fake numbers and calls nobody.

**Then look at the form.** Run:

    uv run --no-project --python 3.12 python callback_server.py --dry-run

and open http://127.0.0.1:8787 in your browser. Fill it in with your own details. Nothing rings;
the call it would have made is written to `dry_run_requests.jsonl`. Press Control and C in the
Terminal to stop the server.

**For a real test call, the server has to be reachable from the internet**, because the provider
sends the end-of-call report back to it. Two ways:

- **Testing:** keep it on your Mac and open a tunnel (Cloudflare Tunnel and ngrok both do this;
  each needs its own small install and sign-up). The tunnel gives you an https address: that is
  your `PUBLIC_BASE_URL`. Start the server with `--trust-proxy` so it records the real visitor's
  address. The tunnel only works while your Mac is awake.
- **For real:** one small always-on host (a small virtual server, or an app host like Render,
  Railway or Fly.io; check current pricing on their sites). It must keep files between
  restarts, because `leads.csv` and the consent records live on its disk. Start it with
  `python3 callback_server.py --host 0.0.0.0 --port 8787 --trust-proxy` behind the host's https.

Then **call yourself first**: fill in the form with your own number and let the assistant ring
you. Try saying "stop" on one call to check it hangs up and puts your number on `dnc.txt`.

---

## Step 7. A new QR that opens the form

The cards you have now open FD's Contact page. This needs its own QR that opens your form:
`https://<your server address>/?ref=omarie`. Ask Claude to make a "callback" version of the card
with that address once the server has its final address, so the printed QR never has to change.
Keep the old cards too: they still work for people who would rather book on FD's site.

---

## Step 8. Do Not Call and opt-outs (check these before going live)

- **Saying stop on a call**: the assistant says goodbye, hangs up, and the number goes on
  `dnc.txt`. That number is never called again by this system. Test it (Step 6).
- **Someone asks you or the shop to stop** by text, email or in person: add a line to `dnc.txt`
  by hand in this form: `+17025551234	2026-11-24	asked Omarie by text`. Do it the same day.
- **Wrong person**: the assistant apologises and the number goes on `dnc.txt` the same way.
- **A number on `dnc.txt` fills the form in again**: it is logged and you get a note, but the
  assistant does not call. You decide by hand.
- **The national Do Not Call list**: these people asked for the call on the form and ticked the
  consent box, which is what allows the call. That only covers this request about their car.
  Never use these numbers for other marketing or hand them to anyone but FD.
- **Texts**: the system texts only you, not the customer. If you or FD later text customers from
  the provider's number, STOP replies must be honoured there too (most providers do it
  automatically; check yours).
- **Keep the records**: never delete `leads.csv`, `consent_log.jsonl`, `consent_texts.json` or
  `dnc.txt`. They prove each person agreed to the call. Keep them at least five years.
- **Changing the consent wording**: change it in `index.html` and give it a new version (both the
  hidden field and `data-version`). The server refuses to start if the words change but the
  version does not, so old leads always point to the words they agreed to.

This is a careful setup, not legal advice. Before the first real call, it is worth having a
lawyer who knows US calling rules (TCPA) read the consent box and the opening line once.

---

## Step 9. Go-live checklist

- [x] Nate's approval (Step 0: covered by Omarie, 25 Nov 2026)
- [ ] `test_callback.py` shows ALL PASS
- [ ] A real call to your own phone works, and the summary reached you
- [ ] Saying "stop" put your number on `dnc.txt`
- [ ] The server's address is https and stays on (not a tunnel)
- [ ] The new QR opens the form, tested on two phones
- [ ] `leads.csv` and the logs are not in git (they hold real people's numbers)
