from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlencode, urlparse

from playwright.sync_api import APIResponse, BrowserContext

from .config import API_BASE, PROJECT_SYMBOL


def build_list_url(page_number: int) -> str:
    parameters = [
        ("projectSymbol", PROJECT_SYMBOL),
        ("term", ""),
        ("comment", ""),
        ("idOrPrefix", ""),
        ("dateFrom", ""),
        ("dateTo", ""),
        ("contributionSymbol", ""),
        ("assignedUserId", ""),
        ("issuer", ""),
        ("replySideFilter", "allReplies"),
        ("page", str(page_number)),
        ("sortField", "date"),
        ("sortDir", "desc"),
    ]

    return f"{API_BASE}/issue?{urlencode(parameters)}"


def build_detail_url(issue_id: int) -> str:
    query = urlencode({"projectSymbol": PROJECT_SYMBOL})
    return f"{API_BASE}/issue/{issue_id}?{query}"


def is_project_issue_request(url: str) -> bool:
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.netloc == "api.feedybacky.com"
        and parsed.path.startswith("/issue")
        and f"projectSymbol={PROJECT_SYMBOL}" in url
    )


def capture_api_headers(
    request_headers: dict[str, str],
) -> dict[str, str]:
    """Zachowuje nagłówki potrzebne do odtworzenia zalogowanego GET-a."""
    valid_header_name = re.compile(
        r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$"
    )

    allowed_names = {
        "authorization",
        "accept-language",
        "origin",
        "referer",
        "user-agent",
    }

    result: dict[str, str] = {}

    for name, value in request_headers.items():
        lower_name = name.lower().strip()

        if not valid_header_name.fullmatch(lower_name):
            continue

        if lower_name in allowed_names or lower_name.startswith("x-"):
            result[lower_name] = value

    result["accept"] = "application/json, text/plain, */*"
    result["cache-control"] = "no-cache"
    result["pragma"] = "no-cache"

    return result


def api_get_json(
    context: BrowserContext,
    url: str,
    headers: dict[str, str],
    retries: int = 3,
) -> Any:
    """Wykonuje wyłącznie GET przez klienta HTTP Playwrighta."""
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        response: APIResponse | None = None

        try:
            response = context.request.get(
                url,
                headers=headers,
                timeout=60_000,
                fail_on_status_code=False,
            )

            status = response.status

            if status in (401, 403):
                raise RuntimeError(
                    f"Brak autoryzacji HTTP {status}. "
                    "Token lub sesja nie zostały zaakceptowane."
                )

            if status == 429:
                wait_seconds = attempt * 10
                print(
                    "Serwer ograniczył liczbę zapytań. "
                    f"Czekam {wait_seconds} sekund."
                )
                time.sleep(wait_seconds)
                continue

            if not response.ok:
                body_preview = response.text()[:300]
                raise RuntimeError(
                    f"HTTP {status} dla {url}\n"
                    f"Odpowiedź: {body_preview}"
                )

            return response.json()

        except Exception as exc:
            last_error = exc

            if attempt < retries:
                wait_seconds = attempt * 3
                print(
                    f"Błąd pobierania, próba {attempt}/{retries}: {exc}\n"
                    f"Ponawiam za {wait_seconds} sekundy."
                )
                time.sleep(wait_seconds)

        finally:
            if response is not None:
                response.dispose()

    raise RuntimeError(
        f"Nie udało się pobrać {url}: {last_error}"
    )
