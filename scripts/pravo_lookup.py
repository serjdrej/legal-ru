#!/usr/bin/env python3
"""Look up official-publication events on publication.pravo.gov.ru.

The portal API was unreachable while this script was prepared.  Therefore its
response schema and search-parameter semantics have not been independently
verified.  The script sends a conservative number/text search request and
will only print records when it can identify the requested fields in the JSON
response; otherwise it reports the precise limitation and exits non-zero.
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
TIMEOUT_SECONDS = 10


class LookupError(RuntimeError):
    """An API or response limitation that must not be hidden from the user."""


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
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "legal-ru-pravo-lookup/1"})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
    except HTTPError as exc:
        detail = exc.read(300).decode("utf-8", "replace").strip()
        suffix = f" Response excerpt: {detail}" if detail else ""
        raise LookupError(f"HTTP {exc.code} from Document/Get ({exc.reason}).{suffix}") from exc
    except URLError as exc:
        raise LookupError(f"Network error reaching Document/Get: {exc.reason!s}") from exc
    except TimeoutError as exc:
        raise LookupError(f"Timed out after {TIMEOUT_SECONDS} seconds reaching Document/Get.") from exc

    if status < 200 or status >= 300:
        raise LookupError(f"Unexpected HTTP status {status} from Document/Get.")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        sample = body[:300].decode("utf-8", "replace").replace("\n", " ")
        raise LookupError(
            f"Document/Get returned non-JSON data (Content-Type: {content_type or 'not supplied'}; "
            f"excerpt: {sample!r})."
        ) from exc


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
            "Search the official publication portal. Development verification found the portal API "
            "unreachable, so the live JSON schema and query semantics remain unconfirmed."
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
    return parser


def main() -> int:
    args = make_parser().parse_args()
    if args.command == "search":
        return run_search(args.query)
    return run_amendments(args.number)


if __name__ == "__main__":
    raise SystemExit(main())
