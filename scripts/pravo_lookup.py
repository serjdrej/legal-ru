#!/usr/bin/env python3
"""Look up official-publication data on publication.pravo.gov.ru.

Confirmed reachable and working from a Russian network (browser test,
2026-09-10) -- a plain GET to /api/PublicBlocks/ returns JSON with no key and
no auth. It is NOT reachable from every network: outbound calls from this
project's own sandboxed agents (Claude's fetch tools, Codex's own sandbox
with network "enabled") all time out on this host, which reads as a
geo-block on non-Russian egress IPs rather than a broken endpoint. Run this
script on your own machine, not inside an agent's sandbox.

`blocks` targets /api/PublicBlocks/, whose JSON shape was confirmed by a
manual browser test on 2026-09-10 (real field names, no key/auth) -- not by
a successful run of this script itself, since the host is unreachable from
every agent sandbox tried so far. `search` and `amendments` use
/api/Document/Get, whose response schema is NOT independently confirmed at
all -- all three commands only print a result when the requested fields are
recognisable in the JSON response; otherwise they report the precise
limitation and exit non-zero rather than guessing.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://publication.pravo.gov.ru/api/Document/Get"
BLOCKS_URL = "https://publication.pravo.gov.ru/api/PublicBlocks/"
TIMEOUT_SECONDS = 10


class LookupError(RuntimeError):
    """An API or response limitation that must not be hidden from the user."""


def _get_json(url: str) -> Any:
    """Shared GET-and-decode-JSON helper, failing explicitly on any error."""
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "legal-ru-pravo-lookup/1"})
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
            f"Network error reaching {url}: {exc.reason!s}. This host is known to be "
            "unreachable from geo-blocked networks (any agent sandbox used on this "
            "project so far) -- try running this script from your own machine/network."
        ) from exc
    except TimeoutError as exc:
        raise LookupError(
            f"Timed out after {TIMEOUT_SECONDS} seconds reaching {url}. This host is "
            "known to be unreachable from geo-blocked networks -- try your own machine/network."
        ) from exc

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
    """Fetch the publication-blocks tree (authorities/categories); shape confirmed by
    manual browser test, not by a prior run of this function itself."""
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


def request_documents(query: str) -> Any:
    """Request a small first page, failing explicitly on any transport error.

    ``NumberSearchText`` is deliberately named in the request instead of
    presenting it as a confirmed API contract: the API was unavailable during
    development and this parameter must be rechecked when connectivity returns.
    """
    params = {
        "NumberSearchText": query,
        "RangeSize": "20",
        "CurrentPageNumber": "1",
    }
    url = f"{API_URL}?{urlencode(params)}"
    return _get_json(url)


def record_candidates(payload: Any) -> Iterable[dict[str, Any]]:
    """Yield dictionaries that plausibly represent publication records."""
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return
    if not isinstance(payload, dict):
        return
    for key in ("Documents", "documents", "Items", "items", "Data", "data", "Result", "result"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return


def first_string(record: dict[str, Any], names: tuple[str, ...]) -> str | None:
    """Return a non-empty string from known field-name variants only."""
    for name in names:
        value = record.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def print_records(payload: Any) -> None:
    records = list(record_candidates(payload))
    if not records:
        top_keys = ", ".join(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        raise LookupError(
            "Document/Get returned JSON, but its record-list shape is not recognised "
            f"(top-level: {top_keys}). The API schema needs manual re-verification."
        )

    printed = 0
    for record in records:
        number = first_string(record, ("Number", "DocumentNumber", "number", "documentNumber"))
        date = first_string(record, ("SignDate", "DocumentDate", "Date", "signDate", "documentDate", "date"))
        authority = first_string(
            record,
            ("SignatoryAuthority", "SignatoryAuthorityName", "Authority", "signatoryAuthority", "authority"),
        )
        link = first_string(record, ("Url", "URL", "DocumentUrl", "PublishedUrl", "url", "documentUrl", "publishedUrl"))
        if not all((number, date, authority, link)):
            continue
        print(f"Номер: {number}")
        print(f"Дата: {date}")
        print(f"Подписавший орган: {authority}")
        print(f"Опубликованный текст: {link}")
        print()
        printed += 1

    if not printed:
        fields = sorted({key for record in records for key in record})
        raise LookupError(
            "Document/Get returned record dictionaries, but none contained all required "
            "number, date, signing-authority and published-text-link fields. "
            f"Fields observed: {', '.join(fields) or 'none'}."
        )


def run_search(query: str) -> int:
    try:
        print_records(request_documents(query))
    except LookupError as exc:
        print(f"Lookup failed: {exc}", file=sys.stderr)
        return 2
    return 0


def run_amendments(number: str) -> int:
    print(
        "The portal is an official-publication register, not a consolidated-current-text service. "
        "Its direct amendment-relation API was not verifiable during development. "
        "This command therefore searches publication events by the base law number; it cannot claim "
        "to be a complete amendment list. Manually review the returned acts and their texts, then "
        "check the current consolidated redaction in an authoritative legal-information source.",
        file=sys.stderr,
    )
    return run_search(number)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Query the official publication portal (publication.pravo.gov.ru). Run this on your own "
            "machine, not inside an agent sandbox -- the host is unreachable from every sandbox tried "
            "on this project so far (reads as a geo-block). 'blocks' targets an endpoint whose shape "
            "a manual browser test confirmed (not a run of this script); 'search'/'amendments' use an "
            "endpoint whose response schema is not independently confirmed at all. All three report "
            "precisely what they can't recognise rather than guess."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    search = subparsers.add_parser("search", help="search published acts by a free-text query or law number")
    search.add_argument("query", help="free-text query or law number, for example 98-ФЗ")
    amendments = subparsers.add_parser(
        "amendments",
        help=(
            "search publication events by base-law number; not a complete amendment list because "
            "a direct relation endpoint was not verified"
        ),
    )
    amendments.add_argument("number", help="base law number, for example 98-ФЗ")
    subparsers.add_parser(
        "blocks",
        help="list publication blocks (issuing authorities/categories) -- shape confirmed by manual browser test, not by a script run",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()
    if args.command == "search":
        return run_search(args.query)
    if args.command == "amendments":
        return run_amendments(args.number)
    return run_blocks()


if __name__ == "__main__":
    raise SystemExit(main())
