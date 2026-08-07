"""Obsługa logowania w oknie przeglądarki i weryfikacja sesji."""
from __future__ import annotations

import time

from playwright.sync_api import BrowserContext, Page

from .api import api_get_json, build_list_url


def wait_for_login(
    page: Page,
    captured_headers: dict[str, str],
    timeout_seconds: int = 600,
) -> None:
    print()
    print("Otwieram Feedybacky.")
    print("Zaloguj się spokojnie w otwartym oknie Chromium.")
    print("Po pełnym zalogowaniu otwórz listę zgłoszeń.")
    print("Program czeka maksymalnie 10 minut.")
    print()

    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        if captured_headers.get("authorization"):
            print("Wykryto poprawne, zalogowane żądanie API.")
            print("Przechwycono nagłówek Authorization.")
            return

        if page.is_closed():
            raise RuntimeError("Okno Chromium zostało zamknięte.")

        page.wait_for_timeout(500)

    raise TimeoutError(
        "Nie wykryto zalogowanego żądania API z Authorization. "
        "Zaloguj się i otwórz listę zgłoszeń."
    )


def verify_session(
    context: BrowserContext,
    headers: dict[str, str],
    start_page: int,
) -> None:
    print()
    print("Sprawdzanie sesji przez bezpośredni GET API...")

    payload = api_get_json(
        context,
        build_list_url(start_page),
        headers,
        retries=1,
    )

    if not isinstance(payload, list):
        raise RuntimeError(
            "Testowy GET zadziałał, ale API nie zwróciło listy JSON."
        )

    print(
        f"Sesja działa. Testowa strona zwróciła {len(payload)} rekordów."
    )
