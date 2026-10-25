# Casting

`references/panels.json` is the authority on who each panel is: its question,
seat list, spread rules, disposition floors, whether it may be cast from real
people, and which extra report block it must fill. The picker writes which
panels run, at what headcount, and whether real-people research is on for any of
them into `run.config.json`. This file adds what does not fit in JSON: the
spread rules for the four core panels and the protocol for the optional
real-people mode.

Cast against the **product brief** from recon, never against a generic
template. A swarm for a video tool and a swarm for a compliance dashboard share
nothing but the headcounts.

| Panel | id | Default size | May be cast from real people |
|---|---|---|---|
| Everyday users | `general` | 10 | no |
| Commercial users 16-49 | `commercial` | 10 | no |
| Researchers | `research` | 10 | opt-in |
| Capital | `capital` | 12 | opt-in |
| Marketing | `marketing` | 8 | no |
| Advertising | `advertising` | 8 | no |
| Consumers | `consumers` | 12 | no |
| Retail and distribution | `retail` | 8 | no |
| B2B buyers | `b2b` | 8 | no |
| Enterprise IT | `enterprise_it` | 6 | no |
| Regulators and counsel | `regulators` | 6 | no |
| Institutions and education | `education` | 8 | no |
| Press and critics | `press` | 8 | opt-in |
| Creators and industry | `creators` | 10 | no |
| Community and influencers | `community` | 8 | no |
| Talent | `talent` | 6 | no |

Panels with a `seats` list are cast one persona per seat, in order, extending
or trimming to the headcount the picker asked for. Panels without seats are
cast from their spread rules alone. Every panel's `question` is its lens: if a
persona's report could have been written by a persona from another panel, the
casting failed.

## Default: fictional personas

Every persona is invented unless the user turned on real-people research for
that panel. Fictional does not mean generic. Each persona gets a name, an age,
a place, a device, a tech-literacy level, a history that explains their bias, a
disposition and a lens no other persona covers. Ground them in category
research (how people in that role really work, what they pay, which tools they
use), but do not model them on a specific, identifiable person.

Fictional capital, research and press personas are still specific: a fictional
seed investor has a fund type, a stage focus, a ticket range and a thesis; a
fictional researcher has a field and a known position in the debate. Use
invented fund and lab names, or describe the organisation type ("a
London seed fund focused on consumer subscriptions"). Do not put a fictional
person at a real, named fund, lab or newsroom.

## Adding a panel

Append an entry to `references/panels.json` with `id`, `label`, `accent`,
`size`, `can_cast_real_people`, `sees_brief`, `min_hostile`, `min_skeptical`,
`question`, and either `seats` or `spread`. Give it an `extra_block` with
`fields` when its verdict needs structured fields the generic report does not
carry. Nothing else needs touching: the picker lists it, the prompt renderer
asks for its block, the board colours it and renders the block, and the
synthesis picks it up.

---

## Everyday users (`general`)

The people who land on this without being its target audience. They answer
not "is this good" but **"could I use this at all, and would I ever want to"**.

- **Age:** at least one person under 20, at least two over 55, the rest spread
  across 25-54.
- **Tech literacy:** a ladder from "asks their grandchild to install apps" to
  "runs a home server", at least 2 at the bottom. Low-literacy users find the
  blockers everyone else routes around without noticing.
- **Access conditions:** at least 3 on a phone, 1 on a poor connection, 1 with
  an accessibility need (low vision, motor, colour blindness, dyslexia, ADHD),
  1 on an old device or browser.
- **Language:** at least 2 people whose first language is not the product's
  language. Language is a usability surface.
- **Money:** at least 2 for whom the price is a real decision.
- **Relationship:** a first-timer, someone dragged in by a partner or
  colleague, someone who arrived by mistake, someone who tried a competitor.
- **At least 3 arrive skeptical or uninterested.**

## Commercial users 16-49 (`commercial`)

People who would **pay for it or use it at work**. They answer **"does this
survive contact with my actual workflow, and what would I drop for it"**.

- Age strictly 16-49, at least one 16-19 and one 45-49.
- Every one has a **named current tool** they would replace or slot this next
  to, including "a spreadsheet" and "nothing, I do it by hand".
- Mix of contexts: solo freelancer, small studio, agency employee, in-house at
  a large company, student with a side hustle, someone whose employer picks the
  tools.
- At least 2 have a **budget they must justify to somebody else**.
- At least 2 judge on speed, 2 on quality, 1 on legal terms or data ownership.
- At least 3 arrive skeptical.

## Researchers (`research`)

People who study this domain. They answer **"is the claim true, is it new, and
what breaks under scrutiny"**.

- At least 3 from outside the product's home region.
- At least three disciplines relevant to the product. For a creative AI tool:
  ML systems, HCI, media studies, plus ethics or law.
- **At least 3 known critics** of the category. A panel of enthusiasts is
  decorative.
- At least 1 who works on evaluation and measurement: the person who asks how
  you would actually prove this works.
- At least 1 from industry research rather than academia.
- Every researcher fills the `science` block.

## Capital (`capital`)

People who can fund, acquire, distribute or kill it. They answer **"would I put
money in, on what terms, and what do I want in return"**. The twelve seats in
`panels.json` run from a home-region seed fund to a hostile specialist.

- At least 4 hostile or skeptical dispositions.
- At least 4 from outside the product's home country.
- At least 3 women.
- Ticket sizes spanning at least two orders of magnitude, from an angel cheque
  to a fund round.
- Every capital agent fills the `deal` block with numbers. "It depends" is not
  a term sheet. An investor who would not invest at any price still states the
  valuation and the proof that would reopen the conversation.

---

## Optional: real-people research

For `research`, `capital` and `press`, the user may tick **Profile real people
from public sources** in the picker (or ask for it explicitly). This produces
an outreach list with standalone value, and it also carries real risk, so the
rules are strict.

**What it is.** A profile of a real, named professional built only from public,
professional sources: their own website, fund or lab pages, published papers,
talks, interviews, articles they wrote, public portfolio lists. The agent then
*simulates* how that person might react. The simulation is model output, not
the person's opinion.

**Rules.**

1. Only public professional roles: investors, academics, journalists, people
   who speak in public as part of their job. Never private individuals, never
   minors, never anyone whose public footprint is personal rather than
   professional.
2. Only professional information. No home addresses, family, health, private
   social accounts or anything that is not part of their public working life.
3. Every real-person persona carries `real_person: true`, at least 2 `sources`
   URLs and `research_notes` that summarise what the sources establish.
4. Real public statements go only into `public_record[]`, verbatim, each with
   its URL. If a quote cannot be verified at its source, it is left out.
5. Simulated speech lives only in `said[]` and `unsaid[]`, which the board
   labels SIMULATION.
6. If research turns up nothing solid on a candidate, drop them and cast
   someone else. A real name with no findable record is a fictional persona
   wearing a real person's identity, which is the one thing this mode must
   never produce.
7. The package is marked internal: every artifact carries the real-people
   banner from `references/synthesis.md`. It is not for publication, and it
   must never be used to contact people while presenting the simulation as
   their view.

**Research protocol.** Run the research in parallel subagents (one per few
candidates), each with WebSearch and WebFetch, never one by one in the main
context. For each candidate record:

- full name, current affiliation, role, field or fund;
- two or more concrete public works (papers, investments, articles, talks)
  with links;
- their stated position on the relevant question, with the URL where they
  stated it;
- for capital: stage focus, typical ticket, geography, three or more relevant
  portfolio companies, and whether they are currently investing;
- whether they lean advocate, methodologist or critic of this category.

---

## Disposition budget

Each panel declares `min_hostile` and `min_skeptical`. Sum them across the
panels that run, enforce them at cast time, then verify them against the
returned reports. Interested has no ceiling, but if it passes half the swarm,
re-check the casting.

If the reports land much friendlier than the cast dispositions, the agents were
told too much about the product's intent. Check what reached them: the recon
brief goes only to panels with `sees_brief: true` (people who would really
arrive informed), never to user-side panels.

## Lite cast (15)

4 general, 4 commercial, 3 research, 4 capital. Same rules, compressed:

- General: one low tech literacy, one on a phone with an accessibility need,
  one skeptic, one wildcard outside the audience.
- Commercial: one solo, one agency, one enterprise-constrained, one skeptic
  with an incumbent tool.
- Research: one advocate, one methodologist, one critic.
- Capital: one seed fund, one operator angel, one strategic or customer-side
  buyer, one hostile specialist.
