# Synthesis: turning the reports into a decision

Read every agent JSON before writing a word. The synthesis is where the swarm
pays for itself: one agent can be wrong, but a dozen independent contexts that
hit the same blocker is close to fact.

Two standing rules:

- **Count, do not impress.** Every claim names the agents behind it. "7 of 20
  users stopped at the same step (general02, general05, ...)" beats any
  adjective.
- **Do not average.** If the users love what the capital panel hates, that is
  the finding. Report both, then say which side you would follow and why. A
  synthesis that resolves every tension into a mild middle has destroyed the
  data.

Write the synthesis in the report language from `run.config.json` (English by
default). Use agent ids together with names, so the board can link them.

---

## The banner

The banner goes at the top of `report.md`. `build_board.py` writes the matching
one into `index.html` and the package `README.md` automatically.

When **no** panel was cast from real people:

> **FICTIONAL PERSONAS.** Every persona in this run is fictional. They were
> built from category research and do not portray specific, identifiable
> people. Their reactions are simulations by independent model agents, not
> research data.

When one or more panels were cast from real people (name those panels):

> **INTERNAL SIMULATION OF REAL PEOPLE.** The [panel names] panels are based on
> real, named professionals, profiled only from public sources (linked per
> person). Anything marked SIMULATION is model output inferred from those
> sources and is **not a statement by that person**. The PUBLIC RECORD sections
> contain only verbatim, sourced quotes. Internal use only: not for
> publication, distribution or citation.

---

## 1. User-side panels (general, commercial, consumers, creators, education, talent)

One section per panel that ran, then a combined read when two or more ran.

**Consensus.** Anything 3 or more agents hit independently, split into positive
and negative, each line naming the agents. Sort by headcount.

**Blocker table.** Every distinct blocker: how many hit it, which panels,
whether it stopped them or only cost them, and how far into the flow it sits.
Early blockers outrank deeper ones at equal headcount, because nobody
downstream ever saw them.

**Fault lines.** Where panels split, and whether the split runs by age, device,
tech literacy, language or money. Name the axis. Most of these are not
contradictions but two needs that can coexist; saying so prevents a bad fix.

**Completion rate.** Of everyone on these panels, how many completed the main
promise unaided. This one number is the honest headline of the users section.

**The wildcard.** What the agent furthest outside the target audience noticed
that nobody else did.

**What nobody said.** Read every `unsaid` together. Patterns there are things
the product's own framing kept people from saying. This is a separate finding
from anything in `said`.

## 2. Researchers (`research`)

- **Claimed versus demonstrated.** For each substantive claim: demonstrated,
  plausible or unsupported, according to this panel.
- **Novelty.** What is new, what is a repackaging of known work, and the prior
  art they name.
- **Methodological holes.** How would you prove this works. If the panel cannot
  construct an evaluation for the core claim, say so plainly, because investors
  will hit the same wall.
- **Ethics, legal and risk flags** with severity.
- **Standing offer.** Per agent: cite, use, collaborate or criticise publicly.
  Count each.

## 3. Capital (`capital`)

Deliver in this order.

1. **What they would want to happen.** The move each investor would push for,
   grouped, because the room usually splits into two or three incompatible
   visions.
2. **What they would refuse.** Red lines, dilution limits, structures they will
   not sign. Anything three or more share is a constraint on strategy.
3. **Would they come in, and on what terms.** The deal table, one row per
   investor, sorted by conviction:

   | Investor | Entry | Ticket | Valuation | Instrument | Conditions | Red lines |
   |---|---|---|---|---|---|---|

   Entry is **YES** (would commit now), **CONDITIONAL** (states the exact
   trigger) or **NO** (states the valuation and proof that would reopen it).
   No blanks.
4. **What they bring beyond money.** Concrete only. "Experience and network" is
   noise; "intros to three buyers in their portfolio" is an asset.
5. **Valuation.** The distribution, not one number: lowest, highest, median,
   where the cluster sits. Then the honest read of what a round would look like
   if the team went out tomorrow, and the gap to the top of the range.
6. **Killers.** What made the hostile investors hostile, and what more than
   half the room would need before any conversation. These outrank every
   feature request in the report.

## 3b. Every other panel that ran

Same shape, driven by the panel's `question` and its `extra_block` fields:
consensus, blockers, the decision count, then a summary in that panel's own
currency. Marketing summarises in positioning and acquisition cost, retail in
margin and volume, regulators in exposure and severity, press in the angle they
would take. Do not translate a panel's verdict into generic product feedback;
the reason it was cast is that it judges in a currency the others do not use.

## 4. Cross-group

- **Science versus money.** Where researchers call a claim unsupported while
  investors price it as proven. If this gap exists it leads the section: it is
  the most dangerous thing a product can carry into a raise.
- **Money versus users.** Where investor priorities would damage the
  experience the swarm just measured. Name the trade and pick a side.
- **Ranked action plan, 1-10.** Per item:

  ```
  1. **[THE CHANGE]**
     Unlocks: general03 Name (reason), capital02 Name (reason)   (7 of 34)
     Panels: general, capital
     Effort: low | medium | high
     Impact: critical | high | medium, and what concretely changes
  ```

  Rank by doors opened: a change that flips a capital agent from NO to
  CONDITIONAL, or removes a blocker six users hit, outranks anything that makes
  a friendly agent slightly happier.

- **The power move.** One non-obvious action that shifts the whole room:
  positioning, a hire, a partnership, a reframing, something to stop doing. Not
  a feature.

## 5. Gaps

List every persona whose report is missing or who never reached the product
(`visited: false`), with the reason from their evidence. They are excluded from
every count above.

## 6. Outreach (real-people runs only)

Only when real-people research was on. Label it clearly as research output,
not simulation. Every real person cast: name, role, organisation, focus, typical
ticket or research area, geography, source links, and their verbatim public
statements from `public_record`. Then a short read on whom it would make sense
to contact, in what order and with what angle, based on their real, stated
thesis, never on the simulation.
