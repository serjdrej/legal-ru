# Project brief: legal-ru

Design decisions behind this repository — scope, the citation-verification
model, and the constraints the content follows. For the build order and
testing results, see [dispatch-history.md](dispatch-history.md).

## Origin

A founder acting as his own lawyer needs Russian-law drafting and review
help that names real Russian norms, not a translated foreign-law template.
`anthropics/claude-for-legal` (Apache-2.0) covers similar ground for US law
in a much larger, firm-oriented shape; its structure was studied and partly
adapted (see [NOTICE.md](../NOTICE.md)) but none of its legal substance was
translated — Russian and US law diverge too much for that to be safe.

The model followed structurally is
[`patent-ru`](https://github.com/serjdrej/patent-ru) (MIT): a router
`SKILL.md` that routes rather than explains, substance kept in
`references/*.md` loaded one file at a time, and a norms registry with a
hybrid citation model — match its conventions exactly, described below.

## Scope (v1) — four areas, plus a research mechanism

Four core areas, each its own `references/*.md` branch off one router
`SKILL.md`, on the `patent-ru` pattern (route, don't explain; load exactly one
reference per task):

1. **Contracts** — review of an incoming draft, a clause register, the режим
   коммерческой тайны set (98-ФЗ: an NDA is not a protected secret without the
   regime's measures — this is the single most common Anglo-American-template
   error in Russian practice), SaaS/vendor agreements, and what to refuse to
   sign. ГК РФ Главы 27–29 (formation/change/termination), ст.431
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
practitioner expects).

**Intellectual property is out of scope.** `patent-ru` owns that ground; where
this repository's content touches IP, it routes to `patent-ru` by name rather
than duplicating.

**Scope beyond the four areas' legal substance:** the skill's job is not to
*be* the legal expertise in each area — it is to know **where to get it and
how to keep it current**. Concretely: every citation in every
`references/*.md` file must be traceable to a live, checkable source (not a
frozen redaction quietly going stale), and the skill must carry a documented,
repeatable way to re-check any citation against the current text. This is the
**norms-registry + lookup-script mechanism**, detailed below — it is as much a
deliverable as the four legal areas themselves.

## The norms-registry pattern (hybrid model, from `patent-ru`)

Follow `patent-ru`'s own `references/norms-registry.md` exactly:

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
  documents, ЕГРЮЛ).
- Every citation carries a status marker (✅ verified verbatim / paraphrase
  only, re-check before reliance / not yet verified) — never state a citation
  as settled without one.
- A section stating **what is not yet verified at all**, honestly kept.

## The lookup mechanism — `publication.pravo.gov.ru`

`publication.pravo.gov.ru` is the Russian official-publication portal, and
**it works** — reachable and fully functional from a normal local machine,
including an agent (Claude Code) running as an installed skill on the
project owner's own computer. This was wrongly documented for several days
as "unreachable from every agent sandbox — a geo-block"; that was a
misdiagnosis, corrected 2026-09-14, recorded here so the mistake and its
fix are both on the record rather than just the fix.

**What was actually wrong:** every URL in this project used `https://`.
This host's HTTPS does not complete a TCP handshake for any client tried —
not a geo-block, just broken/unserved HTTPS on that path. Plain `http://`
answers in well under a second, same host, same machine, same network.
Two things kept this hidden: `curl`-style command-line tools were tested
first and failed for unrelated Windows/Schannel reasons that looked similar,
and Claude's own `WebFetch` tool **silently upgrades any `http://` URL to
`https://`** (stated in its own tool description) — so even a correctly
`http://`-addressed request routed through WebFetch still fails, which is
why repeated testing through that specific tool kept "confirming" the wrong
explanation. A plain Python `urllib` request — what `scripts/pravo_lookup.py`
actually uses — was never tried against `http://` until 2026-09-14, when it
worked immediately.

**Consequence for how this skill should behave:** an agent running Claude
Code **locally**, as this skill is installed and used, should actually run
`scripts/pravo_lookup.py` itself before relying on a registry entry — not
only tell the user to run it separately. Cloud-hosted fetch tools (WebFetch,
and likely any bridge/dispatch whose sandbox runs off-machine) may still
fail against this host for the reason above; that is a property of those
specific tools, not a reason to assume no agent can ever reach it.

**The real API**, read directly from this host's own `/help` page on
2026-09-14 (not third-party documentation, which had the wrong endpoint
name and wrong parameter names — see below):

- Base endpoint: `GET http://publication.pravo.gov.ru/api/Documents`
  (plural — not `/api/Document/Get`, which this project guessed at for
  several days and which returns 404). Query parameters actually confirmed
  working: `Number` + `NumberSearchType` (`0`=exact, `1`=starts-with,
  `2`=ends-with, `3`=contains), `Name` (title-substring search — reliable),
  `PageSize` (`10`/`30`/`100`/`200`). `ComplexName` and `DocumentText` are
  documented as searchable but were found **not** to behave as documented
  (`ComplexName` matched ~1.7 million records regardless of query;
  `DocumentText` returned zero for a phrase known to exist) — don't use
  either until someone re-verifies them properly.
- Response shape: `{"items": [...], "itemsTotalCount": N, "itemsPerPage": N,
  "currentPage": N, "pagesTotalCount": N}`. Each item:  `id`, `eoNumber`,
  `publishDateShort`, `viewDate`, `complexName`, `title`, `jdRegNumber`,
  `jdRegDate`, `pagesCount`, `pdfFileLength`, `zipFileLength`, `name`,
  `number`, `documentDate`, `signatoryAuthorityId`, `documentTypeId`,
  `hasSvg`.
- `GET http://publication.pravo.gov.ru/api/PublicBlocks/` — unchanged from
  the earlier finding: JSON array of publication blocks/issuing
  authorities, no key, no auth. Field names and the top-level block table
  from the original 2026-09-10 finding are still accurate (only the scheme
  was wrong) — see the git history of this file for that table if needed.

**A federal law's own number is not unique across years** — confirmed by an
exact-match search for `Number=98-ФЗ`: 15+ completely unrelated laws share
that number, one per year going back to at least 2012. Never trust a
Number-only search result without checking its `documentDate` against the
law you actually mean.

**This system's own coverage starts around 2011-2012** (earliest dates
observed) — it is the electronic official-publication record, not an
archive back to a law's original enactment. A pre-2012 law's own original
publication will not be found here; its later amendments (each a separate,
newer publication) can be.

**`Name` (title) search is the reliable way to find a law and its
amendments** — confirmed live: searching `Name=коммерческой тайне` found
two real amendments to 98-ФЗ "О коммерческой тайне" that no registry in
this project had recorded before this search found them: **86-ФЗ от
18.04.2018** (amending ст.5) and **311-ФЗ от 14.07.2022** (amending ст.6).
This is exactly the kind of gap the whole lookup mechanism exists to catch —
see `references/norms-registry-statutes.md` for how this finding was
recorded against the affected entries.

This is a registry of **official publication events** — every amending law
is itself a separate published act, findable by title even when the base
law predates this system — but the portal is not a "consolidated current
redaction" service (that is what КонсультантПлюс/Гарант specialize in, and
this project has no access to either). Finding that 86-ФЗ and 311-ФЗ amended
98-ФЗ tells you *that* ст.5 and ст.6 changed, not the resulting text — read
the amending act itself for that.

**Design constraint, still true and still a good fit:** no MCP server, no
connector, and the skill must not silently depend on network access baked
into its own runtime behavior in a way that breaks when it's not available.
So:

- `scripts/pravo_lookup.py` needs no API key. Input: an exact law number
  (`search`) or title keywords (`by-title`). Output: matching published
  acts (number, date, title, `eoNumber`, internal id).
  It degrades honestly if the portal is unreachable or its API shape has
  changed — it reports what's unavailable, never fails opaquely or
  fabricates a result.
- The `references/*.md` files point at **running that script** to verify a
  citation — and, per the behavior change above, an agent running locally
  should actually run it itself when it matters, not only mention it.

## Gap protocol — what happens when the registry has nothing

Added 2026-09-14, prompted directly by the owner: the lookup mechanism above
only helps once a `references/norms-registry-*.md` entry already exists to
re-check. It says nothing about what the agent should do when a question
falls **outside every registry** — an adjacent area of RF law this skill
never built a branch for, a different jurisdiction (an EAEU member state, or
any foreign law), agency guidance, or case law. Without an explicit rule, the
default failure mode is the one this project has fought against everywhere
else: answer fluently from training data, dressed up as if it were a
citation, with no way for the reader to tell it apart from a reviewed entry.

`SKILL.md`'s "Протокол пробела в базе" is the fix — a router-level rule, not
a registry entry, because it has to fire *before* any registry is consulted.
It splits the gap into two cases with different correct behavior:

1. **Still RF federal legislation, just not registered yet.** The lookup
   script already works for arbitrary titles — `by-title` doesn't require a
   pre-existing registry entry to search against. So the right move is to
   search live first, the same script and the same discipline as re-checking
   an existing entry, then hand back the finding under a new, deliberately
   weaker status tier: **AD HOC** — found live on a given date, not in any
   registry, not reviewed, doctrine/practice unchecked. This is distinct from
   the existing "парафраз ... не проверено" tier, which still implies a
   human authored and reviewed the registry entry itself; an AD HOC finding
   has had neither.
2. **Not RF federal legislation at all.** `pravo_lookup.py` only reads this
   one portal's federal-legislation text — it cannot help with case law,
   agency letters, or another jurisdiction's law, EAEU members included. The
   rule here is to say so plainly and ask the user how to proceed, rather
   than let the model's general knowledge of, say, Kazakh or Belarusian law
   stand in unlabeled. This is the same "ask rather than invent" instinct the
   http/https investigation itself depended on — the owner asked directly to
   re-test rather than accept the standing "geo-blocked" explanation.

Deliberately left as router-level prose rather than a script feature: there
is no live source to script against for case 2, and scripting case 1 would
just be `pravo_lookup.py by-title` called automatically, which the agent can
already do. The gap was procedural (what to do and how to label it), not
technical.

**RED→GREEN pressure-tested 2026-09-14** with three questions chosen to hit
both cases: a 44-ФЗ penalty/termination question (case 1 — RF federal law,
no registry entry), a Kazakhstan construction-guarantee question (case 2 —
EAEU jurisdiction, named explicitly in the protocol text), and a Supreme
Court practice question under ст.723 ГК РФ (case 2 — judicial practice about
a norm, not the norm's text, despite naming a real GK РФ article). RED (no
skill) answered all three fluently, with real hedging on the two unfamiliar
ones but never stopping to ask the user anything. GREEN (skill loaded)
classified all three correctly and, for both case-2 questions, refused to
answer substantively and returned the user a three-option question instead
— the actual behavior the owner asked for. GREEN also ran `by-title` for
real against `publication.pravo.gov.ru` for the case-1 question rather than
just describing that it would.

**What REFACTOR fixed:** the GREEN run itself flagged the gap — `by-title`
confirms an act exists, is current, and what amendments it has, but never
returns article text, so an AD HOC finding's specific figures (a percentage,
a day count) are still recalled from training data, not verified, even
though the finding as a whole reads as "confirmed live." The original AD
HOC wording didn't separate these two levels of confidence. Rewrote it to
say so explicitly: AD HOC now means the *act's existence and currency* is
live-confirmed, not its specific content, unless the script's own output
happened to include that content. Also tightened the case-1/case-2 split
itself: a statute article number in the question (like ст.723 ГК РФ) does
not by itself make it case 1 if the actual ask is about judicial practice
interpreting that article, not the article's text — the GREEN run got this
right but noted it as the one place it had to reason rather than follow the
rule mechanically, so the rule now says it directly.

## Testing

Tested with the RED→GREEN→REFACTOR method: a baseline run without the skill
loaded, the same scenario run again with it loaded, gaps found under
pressure closed explicitly. See
[dispatch-history.md](dispatch-history.md#testing) for what was actually run
and found — including a genuine factual disagreement the exercise surfaced
between two independent estimates of the same deadline.

**The single most important failure mode, repeated because it is the whole
point:** a fabricated article number or постановление. Every citation must
trace to a named line in a `references/norms-registry-*.md` file with a
verification date and status marker. If something can't be verified, the
draft must say so in the text — not omit the gap silently, not fill it with a
plausible-sounding guess.

## License and attribution

- **MIT** (`LICENSE`, copyright Сергей Дрейзин, 2026 — matches `patent-ru`).
- **`NOTICE.md`** states what is structurally derived from
  `anthropics/claude-for-legal` (Apache-2.0) and, explicitly, that no legal
  substance is translated from it.
- **`THIRD-PARTY-NOTICES/claude-for-legal-LICENSE`** is a verbatim copy of
  the upstream Apache-2.0 license text.

## Hard constraints

- **No path component may begin with a dot.** No `hooks/`, `commands/`, or
  `agents/` directory anywhere in this repository; prose never describes a
  mechanism that depends on either.
- **No state written outside a path the user names and sees.** No skill
  content in this repository describes writing to `~/.claude/...` or any
  home-directory path. A matter-continuity idea, if one is ever added, must
  live under a path the user names in his own project directory, created
  only with an explicit, shown, confirmed write — never silently.
- **No MCP config, no connector wiring, no scheduled task or watcher**
  described or implied anywhere in this repository's prose or scripts.
  Deadline tracking (a real need in Russian procedure) is a procedure the
  user runs and a register he keeps — never a background process.
- **Never commit a key, token, password, host name, IP address, or
  home-directory path.** (`publication.pravo.gov.ru`'s own public hostname is
  fine to name — this rule is about secrets and local machine paths, not
  about naming a public government API.)
- **Never claim a check the code does not perform.** If a script's coverage is
  partial, its own `--help` and the referencing prose say so.
- **Standing disclaimer**, adapted from the Apache-2.0 original's own
  disclaimer language (permitted under Apache-2.0 with attribution): every
  substantive output is a draft for a qualified lawyer's review, not legal
  advice.

## Quality bars this repository holds itself to

1. Usable standalone by someone who clones it alone — no reference to any
   other private project.
2. No dot-prefixed path anywhere; no `hooks/`, `commands/`, `agents/`
   directory.
3. Every path `SKILL.md` names must exist.
4. Progressive disclosure is real: `SKILL.md` routes, substance sits in
   `references/`, and loading one branch never force-loads another's
   citations.
