# The FD marketing team

Written 25 Nov 2026 for Omarie. This adds two engines to `PLAN.md`: business partners
you call yourself, and an AI that calls back people who scan your QR code.
Nothing here calls, texts or posts by itself. Nate approves anything that speaks for FD.

## Who does what

| Role | Who | What they do |
|---|---|---|
| Prospect finder | Done once by Claude | 30 Las Vegas businesses that see exotic owners: `PARTNER-PROSPECTS.csv` |
| Caller | You | Call 5 businesses a day with `CALL-SCRIPTS.md`. Log each call on the PARTNERS tab. |
| AI callback | The callback server | Calls back QR leads within about 2 minutes. Books a time for FD to call them. Texts or emails you. |
| Tracker keeper | You, Monday 20 min | PARTNERS, LEADS and LOG tabs in `FD-referral-tracker.xlsx` |
| Coach | Claude, monthly | Reads the tracker and changes the script only where the log says so |

## Engine 1: business partners (start this week)

1. Open `PARTNER-PROSPECTS.csv`. It holds 30 businesses: rental fleets, detailers, wrap shops,
   dealers, clubs, storage and tracks. 25 have a public phone.
2. Call 5 a day, Tuesday to Thursday. Use the opener for that type of business.
3. The ask is simple: when a customer needs work you don't do, send them to FD with the code OMARIE.
4. Give first. Ask who their best customer is, and send owners you meet their way.
5. Log every call on PARTNERS. Follow up "Call back" and "Interested" on the date you set.
6. Never offer a partner a cut. If they ask, that is Nate's call.

Calls go to businesses only. A number that looks like a personal cell gets checked against the
National Do Not Call Registry first. No AI or recorded voice on these calls.

## Engine 2: AI callback for QR leads (after Nate says yes)

Someone scans the QR and fills in a short form. They tick a box agreeing to an AI call.
The AI calls within about 2 minutes. It says it is an AI, asks about the car and the need,
and books a time for FD to call. It never quotes prices, results or discounts.

What it needs before it goes live (steps in `callback/SETUP.md`):
1. Nate approves the AI speaking for FD, and names who takes the booked calls.
2. You sign up for a calling service (Vapi is the pick) and buy a number. This costs money monthly.
3. Someone hosts the small server, and the QR cards point at its address.
4. A lawyer reads the consent box once (recommended, not checked).

Tested: 17 of 17 dry-run checks pass with fake data. No live call has been made.

## What the research says (`RESEARCH.md`)

Eight YouTube videos were checked. None proves its numbers, and none is about sending
customers to someone else's car shop. The five tactics worth copying:

1. Ask for 30 seconds, then ask where their customers' cars go for work they don't do.
2. Give first: send partners customers before asking for any.
3. Map partner types and name 3 real businesses in each.
4. Spend 5 minutes on each business first and mention one real detail.
5. Use one script, log every call, and change the script only when the log says so.

## Targets for the first month (guesses until the tracker says otherwise)

- 60 business calls, 10 "interested", 3 partners who agree to send people.
- QR leads: depends on cards handed out.
