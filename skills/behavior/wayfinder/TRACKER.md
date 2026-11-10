# Local Markdown Tracker for Wayfinder

KDA uses a file-based tracker so a task workspace stays self-contained. The
map and tickets are ordinary Markdown files; "issue", "label", "assignee", and
"blocking" map to the conventions below.

## Layout

```text
docs/wayfinder/
  map.md                 # the map: destination, notes, decisions, fog, scope
  tickets/
    01-<slug>.md         # one decision ticket per file
    02-<slug>.md
```

## Map

`map.md` follows the body template in `SKILL.md`. Add a YAML block at the top
for machine-readable state:

```yaml
---
kind: wayfinder-map
status: open
created: <YYYY-MM-DD>
---
```

## Tickets

Each ticket file starts with:

```yaml
---
kind: wayfinder-ticket
id: "01"
title: <short title>
type: research | prototype | grilling | task
mode: HITL | AFK
status: open | claimed | closed
claimed_by: <name or empty>
blocked_by: []
---
```

Then the `## Question` body. A ticket is **unblocked** when every id in
`blocked_by` has `status: closed`. The **frontier** is open, unblocked,
unclaimed tickets. Claim a ticket by setting `status: claimed` and
`claimed_by` before doing work.

## Resolution

Append a `## Resolution` section with the decision and evidence links, set
`status: closed`, and add one line to `map.md` under `## Decisions so far`.
Do not paste long evidence into the map; link the ticket or artifact.

## Labels and triage

Use `type` instead of tracker labels. There is no `ready-for-agent` label;
tickets are decisions, not implementation slices. If a ticket turns into
implementation work, create a separate ticket under `.scratch/tickets/` using
the `to-tickets` skill.
