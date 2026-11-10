---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

> **KDA adaptation.** Tickets live in `.scratch/tickets/`; the task contract wins over skill advice; commit only when the user asks. The task contract and independent validation are authoritative. Use the local task workspace paths described in ADAPTATION.md; do not use an external issue tracker. Process record: see `../../PROCESS_LOG.md`.

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, read it from `.scratch/tickets/` and state its title before starting. If the reference is ambiguous, ask.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, call the Skill tool with "code-review" to review the work.

Commit only when the user asks, and keep the commit scoped to the ticket.
