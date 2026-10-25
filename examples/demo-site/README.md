# Larder demo site

A four-page static site for a fictional product, *Larder*: a shared pantry app
for households. It exists only so focus-swarm has something real to visit.

The site contains a few deliberate product problems, so a swarm has something
to find:

- pricing that headlines an annual-billed monthly figure;
- a "free" trial that requires a card, including on the $0 plan;
- low-contrast small print;
- a vague data-sharing line folded into the sign-up sentence;
- a pricing table that does not fit a phone screen.

These notes live here, not in the site's HTML or CSS, so agents that read the
source do not get the answers for free.

## Serve it

```bash
python -m http.server 8765 --bind 127.0.0.1 -d examples/demo-site
```

Then use `http://127.0.0.1:8765/` as the target in the picker. Any free port
works; 8765 is only the one used for the recorded run in
[`../demo-run/`](../demo-run/).

Forms do not submit anywhere. Nothing is collected.
