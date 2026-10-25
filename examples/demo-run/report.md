# Larder: swarm synthesis

> **FICTIONAL PERSONAS.** Every persona in this run is fictional. They were
> built from category research and do not portray specific, identifiable
> people. Their reactions are simulations by independent model agents, not
> research data.

Target: the Larder demo site (four pages, served locally). Cast: 15 agents in 6
panels (general 4, commercial 2, consumers 3, regulators 2, press 1, capital 3).
All 15 reached the site and filed valid reports. Every agent fetched the pages
over HTTP and looked at pre-rendered desktop and phone screenshots
(`visit_method: http`).

**Headline: 0 of 15 completed the main promise, 0 of 15 said yes.** 5 maybe,
10 no. Average usability 39 of 100. Capital: 2 conditional, 1 no. The concept
was liked more than anyone said out loud; the funnel lost every single person
before they saw the product.

---

## 1. User-side panels

### Everyday users (`general`): 0 yes, 0 maybe, 4 no, usability 28

- **Consensus, negative.** Card required before anything is shown: all four
  (general01 Doreen, general02 Kwame, general03 Marisol, general04 Harald).
  "$3.99 a month" is a $47.88 annual charge with the monthly price in an FAQ:
  all four. Pricing table cut off at phone width: all four. No cancel route:
  general01, general02, general03. Pale grey text carries the terms:
  general01, general04.
- **Consensus, positive.** The headline and the pantry mock-up explain the idea
  in seconds: general01, general02, general04 ("the mustard joke landed").
- **Wildcard (general04 Harald, arrived by mistake looking for a shelf).** Two
  things nobody else saw: the expiry tags in the mock-up are red against green,
  so a red-green colour-blind visitor cannot tell "2 days" from "plenty" by
  colour; and the whole page is about Sam, Priya and Jo, so someone who lives
  alone reads it as "not for my kind of kitchen" and leaves.

### Commercial users (`commercial`): 0 yes, 0 maybe, 2 no, usability 28

Both rejected it on fit, not on price. commercial01 Priya runs a 12-person
kitchen and the top plan stops at 10, with no roles, no batch or allergen
fields and no export ("my sheet works"). commercial02 Tom manages 40 student
houses and needs one login, many houses and one invoice to the landlord in
sterling. Both found the $47.88 price trivial and the data clause disqualifying
for business data. Neither is the target today; see fault lines.

### Consumers (`consumers`): 0 yes, 2 maybe, 1 no, usability 52

| Agent | Would pay | Fair price | Walk-away | Buys instead |
|---|---|---|---|---|
| consumers01 Hannah | no | about $3.99/mo if truly monthly | over about $6/mo, or $47.88 up front unseen | her free shared list app |
| consumers02 Jordan | no | about $3/mo, monthly, one-tap cancel | $5.99/mo unseen; $47.88 card-first | a shared phone note |
| consumers03 Linh | no | about $3/mo, monthly, no data sharing | $47.88 card-first, or $5.99 with partner offers | a shared spreadsheet and a weekly call |

The price the market will bear is roughly **$3 to $4 a month, billed
monthly**. The current monthly price ($5.99) sits at or above every walk-away
line. All three compare against something free they already use.

### Blocker table (all 15 agents)

| Blocker | Hit by | Panels | Stopped or cost | Where in the flow |
|---|---|---|---|---|
| Card required before seeing the product, including the $0 Starter button | 15 of 15 | all | stopped | first click on any CTA |
| Headline price is annual-billed; monthly price hidden in a closed FAQ | 15 of 15 | all | cost (stopped general01, general03) | pricing page |
| Pricing table 760 px wide on a 390 px phone; Household cut off, no scroll cue | 13 of 15 | all except the two desktop personas (commercial02, regulators01) | stopped general01, general03, regulators02; cost the rest | pricing page on phone |
| Partner-offer consent bundled into the sign-up line; sharing undefined | 14 of 15 | all except general03 | stopped consumers03, regulators01 | sign-up and privacy |
| No cancellation route stated anywhere | 10 of 15 | general, consumers, regulators, commercial01, capital02 | stopped general01, consumers02 | sign-up |
| No link to the web app that "works today"; no real screenshots; video placeholder | 9 of 15 | capital, press, general02, general04, consumers01, commercial02 | stopped capital01, capital03, press01, general04 | home page |
| Legal and billing text in #9aa59f on white (about 2.5:1) | 9 of 15 | general01, general04, consumers02, consumers03, press01, regulators, capital02, capital03 | cost | wherever small print appears |
| Phone nav hides Pricing and Privacy | 8 of 15 | capital01, capital02, consumers02, consumers03, general01, general02, press01, regulators02 | cost | header at phone width |
| Sign-up silently selects Household whichever plan was clicked | 7 of 15 | general01, general04, consumers01, consumers03, commercial01, regulators02, capital03 | cost | sign-up |
| "Terms" not linked; no Terms page | 6 of 15 | commercial02, consumers03, regulators, press01, capital02 | cost (stopped regulators02) | sign-up |

### Fault lines

- **Device, not age.** Every phone persona hit the clipped pricing table and
  the missing nav; the desktop personas (commercial02 Tom, regulators01 Ines)
  did not. The fix is layout, not audience.
- **Household shape.** The product reads as a flatshare app. general04 (lives
  alone), consumers01 (family of four, "for 25-year-olds"), consumers03
  (buying for elderly parents) and commercial01 and commercial02 (teams and
  landlords) all felt outside the picture. These are different needs that can
  coexist: a single-person mode and a family example are copy and onboarding;
  teams and landlords are a separate product decision.
- **Money.** For general02 Kwame and general03 Marisol, $47.88 in one charge is
  a real risk (overdraft, a previous annual renewal). For commercial01 Priya it
  is "nothing". Annual-by-default hurts exactly the people for whom the price
  is a decision.

### Completion rate

**0 of 15** completed the main promise unaided. Nobody could see a live pantry
without entering a card, and the demo sign-up creates nothing. On a real site
this number would be the share of visitors who reach a working pantry before
the card wall: here, none.

### What nobody said

- **Silent bounce at the card field.** Ten agents describe closing the tab
  without a word to the company (general01, general03, general04, consumers01,
  consumers02, consumers03, commercial02, capital02, regulators02, press01).
  This objection never reaches support or a survey; it shows up only as
  drop-off.
- **The screenshot with no comment.** Eight agents would send the clipped
  pricing table or the consent line to someone else with no caption
  (capital01, capital03, consumers02, consumers03, general03, regulators01,
  regulators02, press01). The product's most shared artefact would be its
  worst one.
- **They liked it more than they admit.** capital01, capital02, capital03,
  consumers02, consumers03, commercial02 and general04 all say the idea is
  better than they would concede in the room. The concept is not the problem.
- **Accessibility failures are reported as personal failures.** general01
  blames her glasses, general03 her English and cracked screen, general04
  stops reading the colour tags, consumers02 says "I got distracted" rather
  than mention ADHD. These users will never file a bug.
- **Shared visibility is also surveillance.** general02 does not want the flat
  to see he buys the cheap stuff, commercial02 sees tenant evidence and tenant
  complaints in the same feature, press01 and regulators01 note that flatmates'
  names and emails enter the system without them seeing any notice.

---

## 2. Regulators and counsel (`regulators`): 0 yes, 0 maybe, 2 no, severity high (2 of 2)

- **Legal basis.** None stated. Contract may cover the core service; partner
  sharing needs separate, freely given consent, which a bundled sentence under
  the button is not (regulators01 Ines, regulators02 Gareth).
- **Questionable data flows.** "Anonymised and aggregated" is used as if it
  were one thing, while the home page promises offers "based on your pantry",
  which needs profiling of an identifiable account. Receipts can reveal health,
  religion or pregnancy. Household members are enrolled without notice.
  Receipt images are kept "to improve recognition", an unstated secondary use.
- **Consumer law.** Annual-as-monthly headline price, prices excluding tax,
  card-captured trial rolling into an annual plan with the condition in a
  footnote, a $0 button that leads to a paid form, no Terms, no cancellation
  route, an unsubstantiated savings claim.
- **Exposure.** A complaint to the data protection or consumer authority is
  the realistic trigger; the partner-sharing line is the likeliest one. Fines
  would be modest at this size; corrective orders would hit the business model.

## 3. Press (`press`): 1 maybe, would not cover yet

press01 Sana's angle: "a fridge app whose second business is shopping data."
The headline she would write: *"'Free for 14 days' costs $47.88: the pantry
app with a card-first trial and a data-sharing clause that names no partners."*
She would not cover it today ("a landing page, not a launch") and has already
saved the pricing footnote and the consent line. What would make it a story:
named partners or a data sheet, or a working app to test what the opt-in sends.

## 4. Capital (`capital`): 2 conditional, 1 no

### 4.1 What they would want to happen

Two incompatible visions:

- **A subscription business carried by household retention** (capital01
  Rebecca, capital03 Aiko). The second household member arrives free and is the
  reason the first one stays; retention is reported monthly; the waste report
  is on every paid plan with a real number.
- **A data business proven by one paying retailer** (capital02 Daniel). Within
  six months, find out whether one retailer pays for aggregated pantry data,
  before building the meal planner; otherwise drop the line.

capital01 states the split directly: choose subscription or retail data as the
main business within 12 months.

### 4.2 What they would refuse

Shared by all three, so effectively a constraint on strategy:

- selling household-level or identifiable purchase data;
- partner consent folded into the Terms;
- growth numbers flattered by card-first trials and annual prepay (capital01:
  no raise on annual prepaid without refund and chargeback rates; capital02: no
  hiding the monthly price and card requirement; capital03: no card-trial
  conversion as the headline metric).

capital01 and capital02 also refuse paid acquisition before the core question
(invite loop or retailer) is answered.

### 4.3 Would they come in, and on what terms

| Investor | Entry | Ticket | Valuation | Instrument | Conditions | Red lines |
|---|---|---|---|---|---|---|
| capital01 Rebecca Lund | CONDITIONAL (4/10) | GBP 250k, up to 400k | GBP 4-6m pre; 3.5m max today | ASA or SAFE with cap, 20% discount | 40% of 300+ households with 2+ active members at week 4; week-8 retention 45%+ for 2+ member households; trial-to-paid 35%+ with a no-card comparison cohort; 85% receipt accuracy on 200 UK receipts | household-level data sales; bundled consent; no raw cohort export |
| capital02 Daniel Hoffmann | CONDITIONAL (4/10) | EUR 30k | EUR 3.0-4.5m pre cap | convertible or SAFE, 20% discount | an LOI or paid pilot from one retailer (EUR 25k+/yr); 2,000 week-4 active households; 25% trial-to-paid; separate unticked consent with a 50-household aggregation floor | data tied to names or emails; consent inside Terms; data revenue with no named retailer |
| capital03 Aiko Matsuda | NO (2/10) | USD 6m in a 20m Series A, if reopened | reopens at USD 28-38m pre | Series A preferred | month-6 paid retention 55%+ on 500+ households, split monthly and annual; 50% weekly active at month 3; measured 25% waste reduction against a control; median saving 1.5x plan price | sharing without separate opt-in; card-trial conversion as headline; unmeasured savings claims |

### 4.4 What they bring beyond money

- capital01: introductions to two UK grocery loyalty teams for opt-in pilots; a
  retention-focused growth lead; a quarterly founders' cohort-data dinner.
- capital02: introductions to the loyalty and category-insight heads at two
  German grocery chains; a review of what retailers actually pay for and
  refuse; a data protection lawyer who has built a loyalty consent flow.
- capital03: a benchmark set of about 40 consumer subscription companies for
  month-3 and month-6 retention; two reference calls with food-waste founders
  who will say where theirs churned; privacy counsel for the consent flow.

### 4.5 Valuation

The cluster is **3 to 6 million pre-money (GBP or EUR) on a SAFE-type
instrument**, with capital01 at no more than GBP 3.5m on today's evidence.
capital03 only names a Series A range, reachable after the proof above. If the
team went out tomorrow with this site and no cohort data: a small pre-seed,
realistically GBP 300-600k at about 3-3.5m pre, with capital01-type funds
taking a call but not leading. The gap to the top of the range is not product
polish; it is one number (multi-member retention at week 8) and one decision
(subscription or data).

### 4.6 Killers

- **No measured number anywhere** (capital03; echoed by capital01 and capital02):
  no retention, no conversion, no savings measurement, only an anonymous quote.
- **The card wall makes any future conversion number suspect** (all three).
- **An undecided revenue model** with the data line hidden from users
  (capital02 wants it proven, capital01 and capital03 want it gone or chosen).

---

## 5. Cross-group

**Science versus money.** No research panel was cast in this run.

**Money versus users.** capital02 wants the partner-data line proven as the
real business; 14 of 15 agents distrust it, and both regulators rate it high
severity. Follow the users at launch. capital02's own conditions (a separate,
unticked consent and an aggregation floor) already require what users ask for,
so the conflict is about timing, not direction: prove opt-in demand first.

### Ranked action plan

1. **Let people in before the card.** Link "Web app works today" to the web
   app; make Starter card-free; move the card to the moment someone chooses a
   paid plan.
   Unlocks: general01 Doreen (her one condition), consumers02 Jordan (impulse
   buyer lost at the card field), capital01 Rebecca (wants a no-card cohort),
   capital03 Aiko (wants to open the product), press01 Sana (needs something to
   test)   (15 of 15)
   Panels: all
   Effort: low to medium
   Impact: critical, it removes the only blocker every agent hit

2. **Say the real price.** Monthly price as the headline with annual as the
   discount, tax included in the local currency, a plan choice on the sign-up
   form instead of a silent Household.
   Unlocks: general03 Marisol (reads the footnote first), consumers03 Linh
   (deal hunter), regulators02 Gareth (drip pricing), capital03 Aiko ("designed
   to be misread")   (15 of 15)
   Panels: all
   Effort: low
   Impact: critical, it is also the most screenshotted problem

3. **Unbundle partner offers.** Remove them from the sign-up sentence; separate,
   unticked opt-in; name partner categories and the fields they receive; set
   an aggregation floor; reconcile "based on your pantry" with "aggregated".
   Unlocks: consumers03 Linh (her deal-breaker), regulators01 Ines (lawful
   basis), press01 Sana (removes the story), capital01, capital02 and capital03
   (a red line for all three)   (14 of 15)
   Panels: all except one general agent
   Effort: low for copy and consent, medium for the data definition
   Impact: critical for the raise, high for users

4. **Fix the phone path.** Stack the plan cards below 760 px, keep Pricing and
   Privacy in the mobile header, use 16 px form inputs so iOS does not zoom.
   Unlocks: general02 Kwame, consumers02 Jordan (gave up on the swipe),
   regulators02 Gareth (Household cut at the price), capital01 Rebecca ("nobody
   tested this on a phone")   (13 of 15)
   Panels: general, consumers, capital, press, regulators, commercial01
   Effort: low
   Impact: high

5. **Show how to cancel, and publish Terms.** One line next to the card field:
   when the first charge happens, how to cancel in two taps, the reminder email
   as a commitment; a real Terms page behind the link.
   Unlocks: general01 Doreen, general03 Marisol, consumers02 Jordan,
   regulators01 and regulators02   (10 of 15)
   Panels: general, consumers, regulators, commercial, capital
   Effort: low
   Impact: high

6. **Make the small print readable.** Raise #9aa59f to at least 4.5:1, put the
   billing terms in body text, and add labels to the colour-only expiry tags.
   Unlocks: general01 Doreen (low vision), general04 Harald (colour
   blindness), consumers03 Linh (tablet), regulators (prominence of key
   terms)   (9 of 15)
   Effort: low
   Impact: high for accessibility, medium overall

7. **Show the product.** Real screenshots, the tour video, a 60-second scan and
   nudge demo, and a named beta household.
   Unlocks: capital01, capital02, capital03, press01, general04, consumers01
   (9 of 15)
   Effort: medium
   Impact: high for capital and press

8. **Publish one measured number, or drop the claim.** Week-8 multi-member
   retention and a measured waste figure from the beta; put the waste report on
   Household; otherwise remove "most households save more than the
   subscription".
   Unlocks: capital01, capital02, capital03 (their first question), press01,
   regulators01, regulators02 (unsubstantiated claim)   (7 of 15)
   Effort: medium
   Impact: critical for the raise

9. **Make the second member free and the invite visible.** Free tier with two
   members; show what the invited person sees before any payment.
   Unlocks: capital01 Rebecca (her thesis), general02 Kwame (the flat can try
   it), consumers01 Hannah (bring her husband in), consumers03 Linh (her
   parents)   (5 of 15)
   Effort: medium
   Impact: high for retention

10. **Decide, out loud, who it is not for yet.** A one-person mode and a family
    example in the copy; a waitlist for teams and landlords instead of silence.
    Unlocks: general04 Harald, commercial01 Priya, commercial02 Tom, consumers01
    Hannah   (4 of 15)
    Effort: low
    Impact: medium

### Power move

**Make "your pantry is never sold" the product promise, and launch without
partner offers.** It turns the one paragraph that unites hostile regulators, a
press angle and three investors' red lines into the brand's differentiator,
removes the consent problem instead of engineering around it, and leaves
capital02's data question to a later, opt-in pilot that can be measured on its
own.

---

## 6. Gaps

None. All 15 personas filed a valid report and reached the target.

## Run notes

- No interactive browser was available, so agents used HTTP fetches and
  pre-rendered desktop and phone screenshots. Sign-up and privacy
  phone screenshots were still rendering when the first wave started; several
  agents judged those two pages from HTML and CSS and said so in their
  evidence.
- The demo site's stylesheet carried a header comment naming the deliberate
  flaws; regulators01 read it ("the stylesheet even says so in a comment").
  The comment has since been moved to `examples/demo-site/README.md` so later
  runs do not see it.
