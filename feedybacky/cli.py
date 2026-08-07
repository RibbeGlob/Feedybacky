from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Playwright, sync_playwright

from .api import capture_api_headers, is_project_issue_request
from .config import BROWSER_PROFILE_DIR, DEFAULT_OUTPUT_DIR, PROJECT_URL
from .paths import ExportPaths
from .scraper import download_details, download_issue_list
from .session import verify_session, wait_for_login
from .storage import write_json
from .transform import flatten_comments


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Eksportuje rozszerzone dane zgłoszeń i komentarzy "
            "z Feedybacky. Program wykonuje wyłącznie żądania GET."
        )
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder wynikowy. Domyślnie: feedybacky_export",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Pierwszy numer strony API. Domyślnie: 1",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=500,
        help="Maksymalna liczba stron. Domyślnie: 500",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Przerwa pomiędzy żądaniami GET. Domyślnie: 2.0 s",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Nie wznawiaj z checkpointu; pobierz szczegóły ponownie.",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help=(
            "Doładuj tylko nowe zgłoszenia do istniejącego zbioru. "
            "Skanuje listę od początku i kończy po kilku stronach bez "
            "nowych ID; szczegóły pobiera wyłącznie dla nowych zgłoszeń."
        ),
    )

    return parser.parse_args()


def run(playwright: Playwright, args: argparse.Namespace) -> None:
    paths = ExportPaths.from_output_dir(args.output_dir)
    paths.ensure_dirs()
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    context: BrowserContext = playwright.chromium.launch_persistent_context(
        user_data_dir=str(BROWSER_PROFILE_DIR),
        headless=False,
        viewport={"width": 1500, "height": 950},
    )

    captured_headers: dict[str, str] = {}
    page = context.pages[0] if context.pages else context.new_page()

    def handle_response(response: Any) -> None:
        if captured_headers.get("authorization"):
            return

        try:
            if not is_project_issue_request(response.url):
                return

            if response.status not in (200, 304):
                return

            request_headers = response.request.all_headers()
            possible_headers = capture_api_headers(request_headers)

            if possible_headers.get("authorization"):
                captured_headers.clear()
                captured_headers.update(possible_headers)

        except Exception:
            return

    page.on("response", handle_response)

    try:
        try:
            page.goto(
                PROJECT_URL,
                wait_until="domcontentloaded",
                timeout=60_000,
            )
        except Exception:
            pass

        wait_for_login(page, captured_headers)

        start_page = max(args.start_page, 0)
        delay_seconds = max(args.delay, 0.2)

        details_resume = (not args.no_resume) or args.incremental

        verify_session(
            context=context,
            headers=captured_headers,
            start_page=start_page,
        )

        issues = download_issue_list(
            context=context,
            headers=captured_headers,
            start_page=start_page,
            max_pages=max(args.max_pages, 1),
            delay_seconds=delay_seconds,
            checkpoint_path=paths.list_checkpoint,
            progress_path=paths.list_progress,
            resume=not args.no_resume,
            incremental=args.incremental,
        )

        if not issues:
            raise RuntimeError("Nie znaleziono żadnych zgłoszeń.")

        records, errors = download_details(
            context=context,
            headers=captured_headers,
            issues=issues,
            delay_seconds=delay_seconds,
            tickets_checkpoint_path=paths.tickets_checkpoint,
            comments_checkpoint_path=paths.comments_checkpoint,
            errors_path=paths.errors,
            raw_dir=paths.raw_dir,
            resume=details_resume,
        )

        comments = flatten_comments(records)
        write_json(paths.tickets, records)
        write_json(paths.comments, comments)
        write_json(paths.errors, errors)

        print()
        print("Eksport zakończony.")
        print(f"Liczba zgłoszeń: {len(records)}")
        print(f"Liczba komentarzy: {len(comments)}")
        print(f"Liczba błędów: {len(errors)}")
        print(f"Folder wynikowy: {paths.output_dir.resolve()}")
        print(f"Zgłoszenia: {paths.tickets.resolve()}")
        print(f"Komentarze: {paths.comments.resolve()}")
        print(f"Surowe rekordy: {paths.raw_dir.resolve()}")

    finally:
        try:
            context.close()
        except Exception:
            pass


def main() -> int:
    args = parse_arguments()

    try:
        with sync_playwright() as playwright:
            run(playwright, args)
        return 0
    except KeyboardInterrupt:
        print()
        print("Przerwano przez użytkownika. Checkpointy zostały zachowane.")
        return 130
    except Exception as exc:
        print()
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 1
