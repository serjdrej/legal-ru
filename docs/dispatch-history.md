# Development history

This document replaces five earlier files (`TASK-01-lookup-and-commercial-secrecy.md`,
`TASK-01b-commercial-secrecy-content.md`, `TASK-02-personal-data.md`,
`TASK-03-corporate.md`, `TASK-04-pre-litigation.md`) that were removed from
this repository, including its history, on 2026-09-10. Those files were
dispatch instructions written for an AI coding agent during development —
they contained machine-specific local filesystem paths and language
addressed to an agent (about non-interactive execution and approval flow)
that has no place in a published repository someone else might clone, open,
or point an agent at. Nothing about the actual decisions or findings they
recorded is removed; it is restated here as plain project history.

## Build order and why

The four branches were built and verified one at a time, not all at once:

1. **Commercial secrecy / NDA (98-ФЗ)** first — the pilot. This is the
   branch the project exists partly because of: the earlier rejection of a
   generic NDA template (`draft-nda` from `phuryn/pm-skills`, refused for
   the library this skill was later split out of) turned on exactly this
   point — an NDA alone does not create a protected commercial secret under
   Russian law without the режим коммерческой тайны measures. Building this
   branch first, completely, let the citation and testing approach be
   validated on one branch before repeating it three more times.
2. **Personal data (152-ФЗ), corporate, pre-litigation** followed, each
   built the same way: a norms registry paraphrasing what a statute
   regulates (never quoting it as settled), a dated "not verified against a
   live source" status on every entry, and a reference file built from that
   registry.
3. **`SKILL.md` was written last**, once all four branches existed, so its
   routing table and its `description` frontmatter could describe real,
   already-built content rather than promising branches that didn't exist
   yet.

## The citation-verification mechanism

Every citation in every `references/norms-registry-*.md` file is marked
with a status — paraphrase vs. verified, and a date — rather than stated as
settled. The intended verification path is `publication.pravo.gov.ru`, the
official Russian legal-publication portal, via `scripts/pravo_lookup.py`,
which the user runs on his own machine.

A material finding from building that script: `publication.pravo.gov.ru`
was **unreachable from every AI-agent sandbox tried during development**
(web-fetch tooling, a plain HTTP client run inside a sandboxed shell, and a
separate coding agent's own network-enabled sandbox all timed out on every
path tried) — consistent with a geo-block on non-Russian egress IPs. It was
confirmed reachable only from the project owner's own browser and network.
One endpoint's exact shape (`/api/PublicBlocks/` — a list of publication
blocks/issuing authorities, real field names, no API key) was confirmed
this way and is wired into `scripts/pravo_lookup.py`'s `blocks` command. A
second endpoint (`/api/Document/Get`, used for `search`/`amendments`) has a
plausible parameter set from third-party documentation but its exact
response schema was never independently confirmed by a live call — the
script is written to fail honestly rather than guess at its shape.

## Testing

The four branches were pressure-tested on 2026-09-10 using the RED→GREEN→
REFACTOR method (see the `writing-skills` skill this approach follows): one
scenario per branch, each built to pressure the single highest-risk item in
that branch under a combination of time pressure and an explicit request to
drop any hedging, run first without the skill loaded (baseline) and then
with it. Three of four baselines answered confidently and unhedged where
they shouldn't have — most notably a baseline run gave an unhedged, wrongly
cited deadline for the 152-ФЗ breach-notification timetable, and a separate
one gave a specific but unverified figure for an ЕГРЮЛ filing deadline. With
the skill loaded, each of those answers carried the correct hedge and a
concrete re-verification step instead. The exercise also surfaced a real
factual disagreement worth recording: two independent, unrelated attempts at
the same question (a baseline test run, and the registry entry itself) gave
different numbers for the ЕГРЮЛ filing deadline — three working days in one,
seven in the other. Rather than picking one, the registry entry was edited
to name both figures and state plainly that neither is confirmed pending a
live check — this is recorded directly in
`references/norms-registry-corporate.md`.

## License and attribution

MIT, matching the sibling skill `patent-ru`. `NOTICE.md` documents what is
structurally adapted from `anthropics/claude-for-legal` (Apache-2.0) and
states plainly that no legal substance was translated from it — every
citation to Russian law here was authored fresh against this repository's
own norms registries.
