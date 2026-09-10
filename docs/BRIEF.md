# Project brief: legal-ru

Consolidated brief for this repository. Read this file before any task brief
that references it — task briefs point here rather than restating this
content.

## Origin

This repository exists to fill a gap identified in the `lazy-skill-library`
project: a Russian-law legal skill for a founder who is his own lawyer, with
the functional reach of `anthropics/claude-for-legal` but none of its
`.claude`-writing, connector/MCP, or schedule/watcher machinery, which made
0 of that project's 151 skills importable. The full original brief is at
`lazy-skill-library/docs/BRIEF-LEGAL-RU-SKILL.md` (not part of this repo —
read it there if you need the complete rationale). This file restates the
decisions that came out of it, made 2026-09-10 with the project owner
(Сергей Дрейзин).

The model to follow structurally is `github.com/serjdrej/patent-ru` (MIT),
installed in the sibling library at
`lazy-skill-library/library/skills/upstream/patent-ru/`. Read its `SKILL.md`
and `references/norms-registry.md` before writing this repository's
equivalents — **match their conventions exactly**, including the hybrid
citation model described below.

## Scope (v1) — four areas, plus a research mechanism

Four core areas, each its own `references/*.md` branch off one router
`SKILL.md`, on the `patent-ru` pattern (route, don't explain; load exactly one
reference per task):

1. **Contracts** — review of an incoming draft, a clause register, the режим
   коммерческой тайны set (98-ФЗ: an NDA is not a protected secret without the
   regime's measures — this is the single most common Anglo-American-template
   error in Russian practice), SaaS/vendor agreements, and what to refuse to
   sign. ГК РФ Части 27–29 (formation/change/termination), ст.431
   (interpretation), ст.333 (penalty reduction), ст.401–406 (liability, force
   majeure).
2. **Personal data** — 152-ФЗ compliance for a data-collecting product:
   policy, consents, the Roskomnadzor notification, 242-ФЗ localisation,
   cross-border transfer rules, the breach-notification timetable.
3. **Corporate** — founders' arrangements, корпоративный договор, minutes and
   written consents, changes that touch ЕГРЮЛ. 14-ФЗ, 208-ФЗ.
4. **Pre-litigation** — претензия, limitation periods, the претензионный
   порядок as a precondition to suit, preclusive procedural terms. АПК РФ,
   ГПК РФ.

Cross-cutting, referenced from all four where relevant: ТК РФ Гл.14
(employee personal data, narrower confidentiality limits than a US
practitioner expects); 135-ФЗ (competition), 44-ФЗ/223-ФЗ (procurement, where
the counterparty is a state/regulated buyer); постановления Пленума ВС РФ and
обзоры practice, cited by number and date where relied on.

**Intellectual property is out of scope.** `patent-ru` owns that ground; where
this repository's content touches IP, it routes to `patent-ru` by name rather
than duplicating.

**The owner's explicit extension to this scope (2026-09-10):** the skill's
job is not to *be* the legal expertise in each area — it is to know **where to
get it and how to keep it current**. Concretely: every citation in every
`references/*.md` file must be traceable to a live, checkable source (not a
frozen redaction quietly going stale), and the skill must carry a documented,
repeatable way to re-check any citation against the current text. This is the
**norms-registry + lookup-script mechanism**, detailed below — it is as much a
deliverable as the four legal areas themselves.

## The norms-registry pattern (hybrid model, from `patent-ru`)

Follow `patent-ru/references/norms-registry.md` exactly:

- **Frequently-amended sources → no inline verbatim text.** ГК РФ, ТК РФ,
  152-ФЗ, 98-ФЗ, and anything amended by ordinary federal law get a **paraphrase
  of what the norm regulates**, never a quoted clause, plus a dated
  "last verified" line and an explicit instruction of what to re-check and
  where.
- **Rarely-amended sources → inline verbatim excerpts are acceptable**, with a
  double-sourced verification date, same as `patent-ru` did for order № 107.
  Judge amendment frequency per source, don't assume — check.
- **A "how to find the current text" section is mandatory**, keyed to a
  **stable entry point**, not a brittle final URL — `patent-ru`'s own text
  warns explicitly that the entry point survives a site redesign and the deep
  link does not. Use `publication.pravo.gov.ru` (see below) as the primary
  stable entry point for federal legislation; name a fallback route for
  anything it doesn't cover (профильные ведомственные акты, ФНС/Роскомнадзор
  documents, ГЭР ЮЛ/ЕГРЮЛ).
- Every citation carries a status marker (✅ verified verbatim / paraphrase
  only, re-check before reliance / not yet verified) — never state a citation
  as settled without one.
- A section stating **what is not yet verified at all** — `patent-ru`'s
  registry has one (§7); this repository's needs the same, honestly kept.

## The lookup mechanism — `publication.pravo.gov.ru`

`publication.pravo.gov.ru` is the Russian official-publication portal.
**Confirmed reachable and working 2026-09-10** — by the project owner, from
his own browser/network, not from any sandbox available to this project's
agents. **Every automated tool tried from this project (Claude's WebFetch,
Bash/curl, and Codex's own `os-sandbox` with network enabled) fails to reach
this host at all, on any path — timeout, not an HTTP error.** Read as a
geo-block on non-Russian egress IPs, not a broken endpoint. Consequence for
every future task: **no dispatched agent can verify a citation against this
API itself.** The owner can, in his own browser or by running
`scripts/pravo_lookup.py` on his own machine. Design and prose accordingly —
a script that fails honestly when unreachable, content that says "re-check
this yourself" rather than "verified", never a task brief that assumes an
agent's own network access will reach this host.

**Confirmed live, by direct test (owner's browser, 2026-09-10):**

`GET http://publication.pravo.gov.ru/api/PublicBlocks/` → JSON array, no key,
no auth. Each element (a "block" = a publishing authority/category), observed
fields: `id` (uuid), `name`, `shortName`, `menuName`, `code`, `description`,
`weight`, `isBlocked`, `parent`, `parentId`, `hasChildren`, `items` (nested
children of the same shape), `isAgenciesOfStateAuthorities`, `imageId`,
`section`, `categories`, `treeViewParentId`. Top-level blocks observed, with
their `id`:

| `code` | `name` | `id` |
|---|---|---|
| `president` | Президент Российской Федерации | `e94b6872-dcac-414f-b2f1-a538d13a12a0` |
| `assembly` | Федеральное Собрание Российской Федерации | `a30c9c82-4a21-48ab-a41d-d1891a10962c` |
| `government` | Правительство Российской Федерации | `19bb10cd-32f3-4632-8303-c94dd5f45359` |
| `federal_authorities` | ФОИВ и ФГО РФ | `28bdeebd-e2cf-45ce-8d2a-2bc1aaadd7fc` |
| `court` | Конституционный Суд Российской Федерации | `b85249b6-f6e6-4562-a783-90ea989af2db` |
| `subjects` | ОГВ субъектов РФ | `022fd55f-9f60-481e-a636-56d74b9ca759` |
| `international` | Международные договоры РФ | `c79f71a1-c367-4e9d-a8b2-046cc8a1673f` |
| `un_securitycouncil` | Совет Безопасности ООН | `f3ddeeb2-0bb5-4f28-989b-e0e8dead6e63` |

`assembly` has children (`hasChildren: true`): Совет Федерации
(`950cdcb1-f55d-4e22-9f05-87074fe08efd`, code `council_1`) and Государственная
Дума (`0dbe1bc1-0e40-446a-a3ba-1ccabe18ca5e`, code `council_2`).

**Still not independently confirmed** (nobody with working network access to
the host has tried these yet):

- `GET /api/Document/Get?...` — search published acts. Parameters seen in
  third-party documentation only: `RangeSize`, `CurrentPageNumber`,
  `NumberSearchType`, `SignDateType`, `PubDateType`, and a `SignatoryAuthorityId`
  filter (now plausible given the confirmed `PublicBlocks` ids above — try
  passing one of the ids in the table). Field names in the response records
  (number/date/authority/link) are still unconfirmed — `pravo_lookup.py`'s
  `search`/`amendments` commands guess at common variants and fail honestly if
  none match; update them once someone with network access reports the real
  response shape.

This is a registry of **official publication events** — every amending law is
itself a separate published act, so searching by a base law's number should
surface its amendment history once `Document/Get`'s shape is confirmed, but
the portal is not a "consolidated current redaction" service (that is what
КонсультантПлюс/Гарант specialize in, and this project has no access to
either).

**Design constraint carried over from the parent project's rules, and it
happens to fit this API well:** no MCP server, no connector, and the skill
must not silently depend on network access baked into its own runtime
behavior. So:

- Write `scripts/pravo_lookup.py`: a script **the user runs himself**, no API
  key needed (confirm this at build time — if the portal does turn out to
  gate some endpoint behind a key, follow the `patent-ru`
  `scripts/keystore.py` pattern for it exactly, do not invent a new one).
  Input: a law's number/date or free-text query. Output: matching published
  acts (number, date, signing authority, a link to the published text) and,
  where feasible, the list of acts that have amended it since.
  It must degrade honestly if the portal is unreachable or its API shape has
  changed since this brief — report what's unavailable, never fail opaquely
  or fabricate a result.
- The `references/*.md` files point the user at **running that script**, or
  at the stable entry point directly, to verify a citation — never present a
  citation as current without that instruction attached.

## Testing — full RED→GREEN→REFACTOR per `writing-skills`

The project owner confirmed (2026-09-10): **full TDD cycle, per sub-skill**,
per the `writing-skills` skill's own methodology (installed at
`lazy-skill-library/library/skills/upstream/superpowers/writing-skills/`).
Summary, for a session that hasn't read that skill in full:

1. **RED** — run pressure scenarios against a subagent **without** the skill
   present; record the baseline behavior and rationalizations verbatim.
2. **GREEN** — write the skill content addressing exactly those failures; run
   the same scenarios again; the subagent should now comply / cite correctly
   / flag what it can't verify instead of guessing.
3. **REFACTOR** — find new rationalizations or gaps under repeated pressure;
   close them explicitly; re-test until stable.

**This loop is Claude's responsibility, not Codex's.** Role split for this
project:

- **Codex** (this and future `work`/`fix` dispatches) drafts the structural
  and substantive artifacts — `SKILL.md`, `references/*.md`,
  `scripts/pravo_lookup.py` — against the literal citations and structure this
  brief and the task brief specify, and self-checks what it can mechanically
  (the acceptance conditions below). It does not run subagent pressure tests
  and does not judge whether a draft is "good enough" — that determination
  belongs to Claude's own verification pass after the dispatch returns.
- **Claude** independently verifies every Codex dispatch (never trusts a
  self-report), then separately runs the RED→GREEN→REFACTOR pressure-test
  cycle described above using its own subagent dispatch. Findings from that
  cycle become new, tightly-scoped `fix` briefs back to Codex.

**The single most important failure mode, repeated because it is the whole
point:** a fabricated article number or постановление. Every citation must
trace to a named line in a `references/norms-registry-*.md` file with a
verification date and status marker. If something can't be verified, the
draft must say so in the text — not omit the gap silently, not fill it with a
plausible-sounding guess.

## License and attribution

- **MIT** (`LICENSE`, already in place — mirrors `patent-ru`, copyright
  Сергей Дрейзин, 2026).
- **`NOTICE.md`** (already in place) states what is structurally derived from
  `anthropics/claude-for-legal` (Apache-2.0) and, explicitly, that no legal
  substance is translated from it.
- **`THIRD-PARTY-NOTICES/claude-for-legal-LICENSE`** (already in place) is a
  verbatim copy of the upstream Apache-2.0 license text.

## Hard constraints (apply to every task brief in this project)

- **No path component may begin with a dot.** No `hooks/`, `commands/`, or
  `agents/` directory anywhere in this repository — a future importer strips
  these and refuses the former; prose must never describe a mechanism that
  depends on either.
- **No state written outside a path the user names and sees.** No skill
  content in this repository may describe writing to `~/.claude/...` or any
  home-directory path. A matter-workspace/practice-continuity idea (adapted
  from the original) must live under a path the user names in his own project
  directory, created only with an explicit, shown, confirmed write — never
  silently.
- **No MCP config, no connector wiring, no scheduled task or watcher**
  described or implied anywhere in this repository's prose or scripts.
  Deadline tracking (a real need in Russian procedure) must be a procedure the
  user runs and a register he keeps — never a background process.
- **Never commit a key, token, password, host name, IP address, or
  home-directory path.** (`publication.pravo.gov.ru`'s own public hostname is
  fine to name — this rule is about secrets and this machine's local paths,
  not about naming a public government API.)
- **Never claim a check the code does not perform.** If a script's coverage is
  partial, its own `--help` and the referencing prose must say so.
- **Standing disclaimer**, adapted from the Apache-2.0 original's own
  disclaimer language (permitted under Apache-2.0 with attribution): every
  substantive output is a draft for a qualified lawyer's review, not legal
  advice.

## Acceptance conditions for the finished repository (do not assert — verify)

(Carried from the parent brief; apply once the repository is feature-complete,
not necessarily to every individual task dispatch.)

1. Own git repository (this one), MIT, `LICENSE` + `NOTICE.md` in place,
   usable standalone by someone who clones it with no reference to
   `lazy-skill-library`.
2. No dot-prefixed path anywhere; no `hooks/`, `commands/`, `agents/`
   directory.
3. Zero dangling references after eventual import into `lazy-skill-library`
   (checked there, not here, via
   `python scripts/import_sources.py --check-library library/skills`).
4. Every path a `SKILL.md` names must exist.
5. `search_skills`-findable for Russian queries a practitioner would type,
   once imported (checked in `lazy-skill-library`, not here).
6. Progressive disclosure is real: state the byte size of `SKILL.md` and of
   every reference file; `SKILL.md` routes, substance sits in `references/`.

## Repository layout (target — build incrementally, one task per area)

```
legal-ru/
  LICENSE
  NOTICE.md
  README.md
  THIRD-PARTY-NOTICES/claude-for-legal-LICENSE
  docs/BRIEF.md              # this file
  SKILL.md                   # router — written last, once branches exist
  references/
    contracts.md
    commercial-secrecy.md    # 98-ФЗ режим коммерческой тайны + NDA
    personal-data.md         # 152-ФЗ
    corporate.md
    pre-litigation.md
    norms-registry-civil.md       # ГК РФ, ТК РФ entries (frequently amended)
    norms-registry-statutes.md    # 152-ФЗ, 98-ФЗ, 149-ФЗ, 14-ФЗ, 208-ФЗ, 135-ФЗ, 44-ФЗ, 223-ФЗ
    norms-registry-procedure.md   # АПК РФ, ГПК РФ, претензионный порядок, sroki
    matter-workspace.md      # the user-directory practice-continuity pattern
  scripts/
    pravo_lookup.py
```

Exact filenames above are a starting proposal, not gospel — a task brief may
refine them; if it does, update this section to match so later briefs stay in
sync.
