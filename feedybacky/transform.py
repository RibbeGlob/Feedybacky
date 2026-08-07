from __future__ import annotations

from typing import Any

from .config import COMMENT_FIELDS, TICKET_FIELDS
from .storage import safe_int


def select_fields(
    source: dict[str, Any],
    field_names: tuple[str, ...],
) -> dict[str, Any]:
    return {field: source.get(field) for field in field_names}


def list_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": safe_int(item.get("id"), default=-1),
        "message": item.get("message") or "",
        "timestamp": item.get("timestamp"),
        "issueIsTerminal": item.get("issueIsTerminal"),
        "issueStatusSymbol": item.get("issueStatusSymbol"),
        "issueStatusName": item.get("issueStatusName"),
        "issueStatusGroupSymbol": item.get("issueStatusGroupSymbol"),
        "issuePrioritySymbol": item.get("issuePrioritySymbol"),
        "reactionTime": item.get("reactionTime"),
        "reactionDelay": item.get("reactionDelay"),
        "lastCommentTimestamp": item.get("lastCommentTimestamp"),
        "lastCommentAuthorProjectRole": item.get("lastCommentAuthorProjectRole"),
        "assignedToMe": item.get("assignedToMe"),
        "messageType": item.get("messageType"),
        "price": item.get("price"),
        "workedTime": item.get("workedTime"),
        "assignedUsers": item.get("assignedUsers") or [],
        "commentCountFromList": safe_int(item.get("commentCount")),
    }


def process_comment(
    ticket_id: int,
    position: int,
    comment: dict[str, Any],
) -> dict[str, Any]:
    result = select_fields(comment, COMMENT_FIELDS)
    result["ticketId"] = ticket_id
    result["position"] = position
    return result


def process_detail_payload(
    issue_from_list: dict[str, Any],
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    detail = payload.get("data")
    comments_payload = payload.get("comments")

    if not isinstance(detail, dict):
        detail = {}

    if not isinstance(comments_payload, list):
        comments_payload = []

    issue_id = safe_int(
        detail.get("id", issue_from_list.get("id")),
        default=-1,
    )

    ticket = select_fields(detail, TICKET_FIELDS)

    for field, value in issue_from_list.items():
        if field in ticket and ticket.get(field) is None:
            ticket[field] = value

    ticket["id"] = issue_id
    ticket["commentCountFromList"] = safe_int(
        issue_from_list.get("commentCountFromList")
    )

    processed_comments = [
        process_comment(issue_id, position, comment)
        for position, comment in enumerate(comments_payload, start=1)
        if isinstance(comment, dict)
    ]

    ticket["commentCountDownloaded"] = len(processed_comments)
    ticket["comments"] = processed_comments

    raw_sanitized = {
        "data": select_fields(detail, TICKET_FIELDS),
        "comments": [
            select_fields(comment, COMMENT_FIELDS)
            for comment in comments_payload
            if isinstance(comment, dict)
        ],
        "internalDiscussion": payload.get("internalDiscussion"),
        "assignedUsers": payload.get("assignedUsers") or detail.get("assignedUsers") or [],
    }

    return ticket, raw_sanitized


def flatten_comments(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []

    for ticket in records:
        ticket_comments = ticket.get("comments")
        if isinstance(ticket_comments, list):
            comments.extend(
                comment
                for comment in ticket_comments
                if isinstance(comment, dict)
            )

    return comments
