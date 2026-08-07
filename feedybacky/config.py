from __future__ import annotations

from pathlib import Path

PROJECT_SYMBOL = "MondiPolska-gbKWcpiIsK"
PROJECT_URL = f"https://feedybacky.com/project/{PROJECT_SYMBOL}"
API_BASE = "https://api.feedybacky.com"

DEFAULT_OUTPUT_DIR = Path("feedybacky_export")
BROWSER_PROFILE_DIR = Path(".feedybacky_browser_profile")

INCREMENTAL_STOP_PAGES = 2

TICKET_FIELDS = (
    "id",
    "message",
    "timestamp",
    "dateCreation",
    "dateClose",
    "closingDate",
    "lastCommentTimestamp",
    "lastCommentAuthorProjectRole",
    "issuePrioritySymbol",
    "issuePriorityName",
    "issueStatusSymbol",
    "issueStatusName",
    "issueStatusGroupSymbol",
    "issueIsTerminal",
    "issuer",
    "messageType",
    "projectSymbol",
    "categories",
    "roles",
    "assignedUsers",
    "assignedToMe",
    "reactionTime",
    "reactionDelay",
    "workedTime",
    "price",
    "issueOrderTypeSymbol",
    "projectServiceType",
    "isIssuingUserNotificationsEnabled",
    "completeness",
    "dateAnonymization",
    "extraInfo",
    "prefix",
)

COMMENT_FIELDS = (
    "id",
    "message",
    "dateCreation",
    "dateLastModification",
    "workedTime",
    "dateWork",
    "userId",
    "userLabel",
    "roleId",
    "roleSymbol",
    "status",
    "is_deleted",
    "isArtificial",
    "isAuthor",
    "isDateWorkDifferent",
)
