# Copy rules

Learned from the shop's corrections. These are not style preferences — getting
them wrong misrepresents what is being sold.

---

## 1. A service is not an inclusion

**The service is the job the shop performs. Everything else came with it.**

A run of identically labelled panels says all the items are the same kind of
thing. They are not, and presenting them as equals hides the actual offer.

| Offer | The service | Included because of it |
|---|---|---|
| Full car PPF | **Full car PPF** | Exterior ceramic coating, interior ceramic coating |
| Windshield PPF | **Windshield PPF**, $899 | Headlight PPF, free |
| Free tune | **ECU calibration** | Free with a RYFT or Opus exhaust |
| Annual package | **The package**, $3,999 | 2 oil, 1 brake, 2 diagnostics, suspension, 10% off |

Write it into the spec value with a kicker:

```bash
--spec 'SERVICE|FULL CAR PPF'
--spec 'INCLUDED|EXTERIOR CERAMIC COATING'
--spec 'INCLUDED FREE|HEADLIGHT PPF'
--spec 'PRICE|$899'
```

Anything with no kicker defaults to `INCLUDED`, which is right for a package
where every line genuinely is an inclusion — the annual service ad relies on
that default and must not change.

## 2. A property is not a service

"Self-healing" describes what the film does. It is not a job anyone performs,
so it never appears in the service run. It can sit in the ticker as a
descriptor of the product.

Same test for anything else: **would the shop write it on an invoice as a line
item?** If not, it is not a service.

## 3. No model names

These ads sell a service and the car is already on screen. Naming the car
spends a line on something the viewer can see, and it makes a service ad look
like a car ad.

## 4. No bordered boxes, ever

Retired. A red-outlined box over film never looks seamless — it looks like a UI
element pasted on. The house treatment is `--spec-style panel`: frosted glass
cropped out of the picture itself, so it moves with the shot.

## 5. Claims need a source

No horsepower figure without a dyno sheet. No partner URL or partner plate
unless that partner's part is actually fitted to the car on screen. The 765LT
cut is on hold for exactly this reason.

---

## Status

| Ad | State |
|---|---|
| Annual service $3,999 · SF90 | **Approved — finished product** |
| Full car PPF · Roma | Rebuilt with the service/included split — awaiting confirmation |
| Windshield PPF $899 · GT3 RS | Rebuilt with the service/included split — awaiting confirmation |
| Free tune · Aventador | Built on glass — awaiting confirmation |
