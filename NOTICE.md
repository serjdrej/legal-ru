# Notice of derivation

This repository (`legal-ru`) is licensed under the MIT License (see `LICENSE`).

Its **structure and conventions** — a router `SKILL.md`, substance kept out of the
router in `references/*.md` loaded one file at a time, checklists, the shape of a
practice-continuity mechanism (a matter-workspace idea, adapted below), and
guardrail/disclaimer language — were studied from and partly adapted from
[`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal),
licensed under the Apache License 2.0. That project's `LICENSE` file is
reproduced in `THIRD-PARTY-NOTICES/claude-for-legal-LICENSE` for reference.

**What was changed, per Apache License 2.0 §4(b):**

- The three mechanisms `claude-for-legal` relies on for continuity of practice —
  writing state under `~/.claude/plugins/config/...`, MCP/connector wiring, and
  scheduled watchers — are not reused. `legal-ru` writes nothing the user did not
  ask for, uses no connector or MCP configuration beyond the read-only skill
  surface, and installs no schedule or watcher. Where the original solved a
  problem with one of these mechanisms, `legal-ru` solves the same problem by a
  different means, described in each affected `references/*.md` file.
- The plugin/skill decomposition is narrowed from the original's twelve plugin
  groups (151 skills, built for firms and in-house departments with attorneys to
  review the output) to four areas built for a single founder acting as his own
  lawyer: contracts (incl. commercial-secrecy regime), personal data (152-ФЗ),
  corporate, and pre-litigation. `law-student`, `legal-clinic`,
  `legal-builder-hub`, and the deeper litigation machinery are not carried over.
  Intellectual property is deliberately out of scope here — see
  [`patent-ru`](https://github.com/serjdrej/patent-ru), which owns that ground.

**What was NOT taken from the original, and must not be assumed present:**

- **No legal substance is translated from the original.** `claude-for-legal`
  analyzes US commercial, privacy, and employment law. None of its legal
  conclusions, checklists' substantive content, clause language, or citations
  were translated or ported into this repository. Every citation to Russian law
  in this repository (ГК РФ, ТК РФ, 152-ФЗ, 98-ФЗ, 149-ФЗ, 14-ФЗ, 208-ФЗ, 135-ФЗ,
  44-ФЗ, 223-ФЗ, АПК РФ, ГПК РФ, and related постановления Пленума ВС РФ) was
  authored fresh, against the norms register in each `references/*.md` file, not
  derived from the Apache-2.0 source.
- No connector, MCP server, hook, command, or scheduled agent from the original
  is present or implied.

This repository is a derivative work as defined by Apache License 2.0 for the
**structural elements listed above only**. It is not a translation, and no
representation is made that any legal analysis in this repository was reviewed
against, or is equivalent to, the original's US-law analysis.
