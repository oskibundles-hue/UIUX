# Adding a client layer

`SKILL.md` holds craft rules that are safe anywhere — thresholds, structure,
label logic, QC. They apply across clients and contain nothing confidential.

Client work needs a second layer that this repository is the wrong home for.

## Why the split

This repository is **public** and the `cli/` directory publishes to npm.
Anything committed here is permanent, indexed, and unretractable — git history
survives deletion.

That makes it the wrong place for:

- Offer terms, promo codes and expiry dates
- Pricing and what each price includes
- Brand names, suppliers and approved-asset links
- **Open claim risks** — any record that live creative carries figures the
  client cannot yet substantiate

The last one is the serious one. A public note saying a client's shipped ads
contain unsourced performance claims is a documented admission, reachable by
anyone, including the people most motivated to find it. Keep it private even
when the fix is already underway.

## Where the client layer should live

Pick one private home per client and keep it as the single source of truth:

- A **private** repository with its own `.claude/skills/<client>-ads/`
- A Claude artifact (private by default) — good when the reference is read by
  people rather than by an agent
- A shared drive folder the team already uses

One home per client, not two. The failure mode is a rule that lives in two
places, gets corrected in one, and quietly disagrees with itself.

## What the client layer should carry

Structure it to answer the questions this skill deliberately does not:

**Approved references** — which shipped cuts are the benchmark, so a new cut
can be compared against something real rather than argued about in the
abstract.

**Brand rules** — typeface and weight, caption size and vertical position as a
percentage of frame height, black floor and midtone targets, grey point, and
any lockup rules for the end card. These are the numbers that make a cut look
like it belongs to the client rather than merely following good practice.

**Offer and expiry ledger** — every cut carrying a date or a promo code, with
the date it dies. Cuts expire silently; nothing in the file itself will warn
you, and an expired offer running live is worse than no offer at all.

**Open claim risks** — figures on screen still waiting on a document, brand
names spelled inconsistently across cuts, superseded logos still in flight.
Mark each one as blocking or not, because the useful question at delivery is
not "is anything open" but "does anything open stop this shipping today".

## Keeping the two layers in step

Reference clause codes (`O-2`, `S-3`, `P-3`) from the client layer rather than
restating the rules. When a threshold changes here, the client layer stays
correct automatically — and when a client genuinely needs a different number,
an explicit override reads as a decision rather than as drift.
