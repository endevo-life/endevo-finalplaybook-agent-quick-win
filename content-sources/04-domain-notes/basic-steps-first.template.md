# Basic steps first — the always-first deterministic sequence

These steps run **in this fixed order, for everyone**, before any situational
branching. They are sequence rules, not questions. Fill in / confirm the
canonical order with Niki.

> Per direction: the two crucial first things are the **doc box** and the
> **legacy contact set up in the phone** — always, before Will/POA/etc.

| # | Step | Domain | Why it's first | Always / conditional |
|---|------|--------|----------------|----------------------|
| 1 | Set up the **doc box** ("docbox") — central place for all documents | digital + physical | Nothing else can be found without it | Always |
| 2 | Set up **Legacy Contact in phone** (Apple/Google) | digital | Fastest, free, unlocks device access | Always |
| 3 | Will | legal | … | Always |
| 4 | POA — financial | legal | … | Always |
| 5 | POA — healthcare / advance directive | legal + physical | … | Always |
| … | (continue) | | | |

## How this becomes code

These map to a fixed-order list in `agent/rules_engine.py` that is prepended to
the situational plan — the member always sees these first, in order, regardless
of which situation profile they match. Confirm the list above and I'll wire it in.
