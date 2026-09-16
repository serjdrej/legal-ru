#!/usr/bin/env python3
"""Look up official-publication data on publication.pravo.gov.ru.

Corrected 2026-09-14 after a real defect was found: every URL in this script
used to be https://, and https:// silently hangs on this host (TCP connect
itself times out) while http:// answers in well under a second. This was
previously misdiagnosed as "unreachable from every agent sandbox -- a
geo-block" -- that was wrong. The true cause: this specific host does not
serve HTTPS in a way any client here could complete a handshake with, but
serves plain HTTP fine, from this project's own local machine and (per the
same test, run again after the fix) still not through cloud fetch tools that
force an http-to-https upgrade (e.g. Claude's own WebFetch tool). A locally
run `python scripts/pravo_lookup.py ...` -- including one invoked by an
agent running as an installed Claude Code skill on this machine, not a cloud
sandbox -- reaches this host and gets real data. Prefer running it yourself
over asserting a citation from memory.

The real API, read from this host's own /help page (not third-party docs)
on 2026-09-14: base endpoint is /api/Documents (plural), not the
/api/Document/Get this script used to guess at. Confirmed working query
parameters used here: Number + NumberSearchType (0=exact, 1=starts-with,
2=ends-with, 3=contains), Name (title substring -- reliable), PageSize.
ComplexName and DocumentText are documented as searchable too but were
found NOT to behave as documented (ComplexName matched ~1.7 million records
regardless of the query; DocumentText returned zero for a known-good
phrase) -- this script does not use either.

**A federal law's own number is not unique across years** -- "98-ФЗ" exists
once per year (2026, 2025, ..., 2012, ...) as completely unrelated laws.
Searching by Number alone, even in exact mode, returns every year's "98-ФЗ".
`search` prints this warning every time and shows the date on every match so
you can tell them apart -- never assume the first result is the one you
meant.

`by-title` searches by (partial) title text instead -- this is the reliable
way to find a specific older law and things that amended it, since an
amending law's own title usually names the law it amends (confirmed: a
by-title search for "коммерческой тайне" found two real amending laws to
98-ФЗ "О коммерческой тайне" -- 86-ФЗ от 18.04.2018 amending ст.5, and
311-ФЗ от 14.07.2022 amending ст.6 -- neither of which any registry in this
project had recorded before this script actually found them).

This system's own coverage appears to start around 2011-2012 (the earliest
dates observed in testing) -- it is the *electronic official-publication*
record, not a historical archive back to a law's original 1990s/2000s
enactment. A pre-2012 law's own original publication record will not be
found here; its later amendments (each a separate, newer publication) can
be, via `by-title`.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DOCUMENTS_URL = "http://publication.pravo.gov.ru/api/Documents"
BLOCKS_URL = "http://publication.pravo.gov.ru/api/PublicBlocks/"
TIMEOUT_SECONDS = 10

NUMBER_SEARCH_EXACT = "0"

NUMBER_RECYCLES_WARNING = (
    "Внимание: номер федерального закона не уникален по годам -- «98-ФЗ» "
    "существует отдельно в каждом году. Ниже показаны ВСЕ совпадения по "
    "номеру с датами; сверяйте дату и название, не берите первый результат "
    "как данность."
)


class LookupError(RuntimeError):
    """An API or response limitation that must not be hidden from the user."""


def _get_json(url: str) -> Any:
    """Shared GET-and-decode-JSON helper, failing explicitly on any error."""
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (legal-ru-pravo-lookup)"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
    except HTTPError as exc:
        detail = exc.read(300).decode("utf-8", "replace").strip()
        suffix = f" Response excerpt: {detail}" if detail else ""
        raise LookupError(f"HTTP {exc.code} from {url} ({exc.reason}).{suffix}") from exc
    except URLError as exc:
        raise LookupError(
            f"Network error reaching {url}: {exc.reason!s}. If this is https, try http "
            "instead (this host has been observed to hang on https while http answers "
            "instantly). If http also fails, you may be behind a network that genuinely "
            "cannot reach this host -- this is not expected on the project owner's own "
            "machine as of 2026-09-14."
        ) from exc
    except TimeoutError as exc:
        raise LookupError(f"Timed out after {TIMEOUT_SECONDS} seconds reaching {url}.") from exc

    if status < 200 or status >= 300:
        raise LookupError(f"Unexpected HTTP status {status} from {url}.")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        sample = body[:300].decode("utf-8", "replace").replace("\n", " ")
        raise LookupError(
            f"{url} returned non-JSON data (Content-Type: {content_type or 'not supplied'}; "
            f"excerpt: {sample!r})."
        ) from exc


def request_blocks() -> Any:
    """Fetch the publication-blocks tree (authorities/categories)."""
    return _get_json(BLOCKS_URL)


def print_blocks(payload: Any, indent: int = 0) -> None:
    """Print the blocks tree recursively: code, name, id, and whether it has children."""
    if not isinstance(payload, list):
        raise LookupError(f"/api/PublicBlocks/ returned {type(payload).__name__}, expected a JSON array.")
    prefix = "  " * indent
    for block in payload:
        if not isinstance(block, dict):
            continue
        code = block.get("code", "?")
        name = block.get("name") or block.get("menuName") or block.get("shortName") or "?"
        block_id = block.get("id", "?")
        print(f"{prefix}[{code}] {name}  (id={block_id})")
        items = block.get("items")
        if isinstance(items, list) and items:
            print_blocks(items, indent + 1)


def run_blocks() -> int:
    try:
        print_blocks(request_blocks())
    except LookupError as exc:
        print(f"Lookup failed: {exc}", file=sys.stderr)
        return 2
    return 0


def _documents_request(params: dict[str, str]) -> dict[str, Any]:
    url = f"{DOCUMENTS_URL}?{urlencode(params)}"
    payload = _get_json(url)
    if not isinstance(payload, dict) or "items" not in payload:
        top = ", ".join(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        raise LookupError(
            f"/api/Documents returned an unexpected shape (top-level: {top}). "
            "The API may have changed since 2026-09-14 -- this needs re-verification "
            "against /help before trusting the output."
        )
    return payload


def _print_items(payload: dict[str, Any]) -> int:
    items = payload.get("items") or []
    total = payload.get("itemsTotalCount", len(items))
    if not items:
        print(f"Совпадений не найдено (itemsTotalCount={total}).", file=sys.stderr)
        return 1
    for item in items:
        number = item.get("number", "?")
        date = item.get("documentDate", "?")
        name = item.get("name", "?")
        eo_number = item.get("eoNumber", "?")
        print(f"№ {number}  от {date}")
        print(f"  {name}")
        print(f"  eoNumber: {eo_number}  id: {item.get('id', '?')}")
        print()
    if total and int(total) > len(items):
        print(f"(Показаны {len(items)} из {total} -- сузьте запрос, если нужны остальные.)", file=sys.stderr)
    return 0


def run_search(number: str, page_size: str) -> int:
    print(NUMBER_RECYCLES_WARNING, file=sys.stderr)
    try:
        payload = _documents_request(
            {"Number": number, "NumberSearchType": NUMBER_SEARCH_EXACT, "PageSize": page_size}
        )
    except LookupError as exc:
        print(f"Lookup failed: {exc}", file=sys.stderr)
        return 2
    return _print_items(payload)


def run_by_title(text: str, page_size: str) -> int:
    try:
        payload = _documents_request({"Name": text, "PageSize": page_size})
    except LookupError as exc:
        print(f"Lookup failed: {exc}", file=sys.stderr)
        return 2
    print(
        "Поиск по названию (Name) -- проверено как рабочий способ найти закон и его "
        "поправки: поправка обычно называет закон, который меняет. Портал -- реестр "
        "публикаций примерно с 2011-2012 года, не архив с даты первоначального принятия "
        "более старых законов. Совпадение подстрочное, без учёта склонения: для кодекса "
        "запускайте и родительную форму ('Гражданского кодекса Российской Федерации'), и "
        "именительную ('Гражданский кодекс') - одна форма молча теряет часть поправок. "
        "Аббревиатуры ('АПК РФ') в официальных названиях не встречаются и дают ноль.",
        file=sys.stderr,
    )
    return _print_items(payload)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Клиент publication.pravo.gov.ru. 'blocks' -- список издающих органов. "
            "'search' -- точный поиск по номеру акта (номер не уникален по годам, "
            "проверяйте дату). 'by-title' -- поиск по названию/ключевым словам -- "
            "надёжный способ найти закон и поправки к нему по смыслу."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="точный поиск по номеру акта, например 98-ФЗ")
    search.add_argument("number", help="номер акта, например 98-ФЗ")
    search.add_argument("--page-size", default="30", choices=["10", "30", "100", "200"])

    by_title = subparsers.add_parser(
        "by-title", help="поиск по названию/ключевым словам -- находит закон и поправки к нему"
    )
    by_title.add_argument("text", help='например "коммерческой тайне" или "персональных данных"')
    by_title.add_argument("--page-size", default="30", choices=["10", "30", "100", "200"])

    subparsers.add_parser("blocks", help="список издающих органов -- проверенный рабочий вызов")

    return parser


def main() -> int:
    args = make_parser().parse_args()
    if args.command == "search":
        return run_search(args.number, args.page_size)
    if args.command == "by-title":
        return run_by_title(args.text, args.page_size)
    return run_blocks()


if __name__ == "__main__":
    raise SystemExit(main())
