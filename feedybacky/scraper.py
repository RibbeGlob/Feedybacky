from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext

from .api import api_get_json, build_detail_url, build_list_url
from .config import INCREMENTAL_STOP_PAGES
from .storage import (
    drop_error,
    load_resume_records,
    read_json,
    safe_int,
    sort_by_id_desc,
    write_json,
)
from .transform import flatten_comments, list_record, process_detail_payload


def download_issue_list(
    context: BrowserContext,
    headers: dict[str, str],
    start_page: int,
    max_pages: int,
    delay_seconds: float,
    checkpoint_path: Path,
    progress_path: Path,
    resume: bool,
    incremental: bool = False,
) -> list[dict[str, Any]]:
    issues_by_id: dict[int, dict[str, Any]] = {}
    first_page = start_page

    if resume or incremental:
        for record in load_resume_records(checkpoint_path):
            issue_id = safe_int(record.get("id"), default=-1)
            if issue_id >= 0:
                issues_by_id[issue_id] = record

    if resume and not incremental and issues_by_id:
        progress = read_json(progress_path, {})
        last_done = (
            safe_int(progress.get("lastPage"), default=-1)
            if isinstance(progress, dict)
            else -1
        )

        if last_done >= start_page:
            first_page = last_done + 1
            print(
                f"Tryb wznowienia listy: {len(issues_by_id)} ID już zebranych, "
                f"kontynuuję od strony {first_page}."
            )

    if incremental and issues_by_id:
        print(
            f"Tryb przyrostowy: {len(issues_by_id)} znanych ID. "
            f"Skanuję od strony {first_page} i kończę po "
            f"{INCREMENTAL_STOP_PAGES} kolejnych stronach bez nowych ID."
        )

    print()
    print("Pobieranie listy zgłoszeń...")

    consecutive_known_pages = 0

    for page_number in range(first_page, first_page + max_pages):
        payload = api_get_json(
            context,
            build_list_url(page_number),
            headers,
        )

        if not isinstance(payload, list):
            raise RuntimeError(
                f"Strona {page_number} nie zwróciła listy JSON."
            )

        if not payload:
            print(f"Strona {page_number} jest pusta. Koniec listy.")
            break

        new_ids_on_page = 0

        for item in payload:
            if not isinstance(item, dict):
                continue

            record = list_record(item)
            issue_id = record["id"]

            if issue_id < 0:
                continue

            if issue_id not in issues_by_id:
                new_ids_on_page += 1

            issues_by_id[issue_id] = record

        ordered = sort_by_id_desc(issues_by_id.values())
        write_json(checkpoint_path, ordered)

        if not incremental:
            write_json(progress_path, {"lastPage": page_number})

        print(
            f"Strona {page_number}: {len(payload)} rekordów, "
            f"nowych ID: {new_ids_on_page}, "
            f"łącznie: {len(issues_by_id)}"
        )

        if incremental:
            if new_ids_on_page == 0:
                consecutive_known_pages += 1
                if consecutive_known_pages >= INCREMENTAL_STOP_PAGES:
                    print(
                        f"Tryb przyrostowy: {consecutive_known_pages} kolejne "
                        "strony bez nowych ID. Kończę skan listy."
                    )
                    break
            else:
                consecutive_known_pages = 0
        else:
            if new_ids_on_page == 0 and page_number != first_page:
                print("Strona nie zawiera nowych ID. Zatrzymuję pobieranie.")
                break

        time.sleep(delay_seconds)

    return sort_by_id_desc(issues_by_id.values())


def download_details(
    context: BrowserContext,
    headers: dict[str, str],
    issues: list[dict[str, Any]],
    delay_seconds: float,
    tickets_checkpoint_path: Path,
    comments_checkpoint_path: Path,
    errors_path: Path,
    raw_dir: Path,
    resume: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    existing_records = (
        load_resume_records(tickets_checkpoint_path)
        if resume
        else []
    )

    records_by_id: dict[int, dict[str, Any]] = {
        safe_int(record.get("id"), default=-1): record
        for record in existing_records
        if safe_int(record.get("id"), default=-1) >= 0
    }

    loaded_errors = read_json(errors_path, []) if resume else []
    errors: list[dict[str, Any]] = (
        [item for item in loaded_errors if isinstance(item, dict)]
        if isinstance(loaded_errors, list)
        else []
    )

    total = len(issues)
    skipped = 0

    print()
    print("Pobieranie pełnych danych zgłoszeń i komentarzy...")

    if records_by_id:
        print(
            f"Tryb wznowienia: znaleziono {len(records_by_id)} "
            "wcześniej zapisanych zgłoszeń."
        )

    for index, issue in enumerate(issues, start=1):
        issue_id = safe_int(issue.get("id"), default=-1)

        if issue_id < 0:
            continue

        if resume and issue_id in records_by_id:
            skipped += 1
            print(f"[{index}/{total}] ID {issue_id}: już zapisane — pomijam")
            continue

        try:
            payload = api_get_json(
                context,
                build_detail_url(issue_id),
                headers,
            )

            if not isinstance(payload, dict):
                raise RuntimeError(
                    "Odpowiedź szczegółów nie jest obiektem JSON."
                )

            ticket, raw_sanitized = process_detail_payload(issue, payload)
            records_by_id[issue_id] = ticket

            write_json(raw_dir / f"{issue_id}.json", raw_sanitized)

            ordered_records = sort_by_id_desc(records_by_id.values())
            write_json(tickets_checkpoint_path, ordered_records)
            write_json(
                comments_checkpoint_path,
                flatten_comments(ordered_records),
            )

            errors = drop_error(errors, issue_id)
            write_json(errors_path, errors)

            print(
                f"[{index}/{total}] ID {issue_id}: "
                f"{ticket['commentCountDownloaded']} komentarzy"
            )

        except Exception as exc:
            errors = drop_error(errors, issue_id)
            errors.append({"id": issue_id, "error": str(exc)})
            write_json(errors_path, errors)
            print(
                f"[{index}/{total}] ID {issue_id}: BŁĄD — {exc}"
            )

        time.sleep(delay_seconds)

    records = sort_by_id_desc(records_by_id.values())

    if skipped:
        print(f"Pominięto już pobrane zgłoszenia: {skipped}")

    return records, errors
