"""Simple rule-based helpers for turning raw bug reports into incidents."""

from app.schemas import BugReport, NormalizedIncident


def normalize_text(value: str) -> str:
    """Trim whitespace and collapse repeated spaces."""
    return " ".join(value.strip().split())


def normalize_tags(tags: list[str]) -> list[str]:
    cleaned_tags: list[str] = []

    for tag in tags:
        cleaned_tag = normalize_text(tag).lower().replace(" ", "-")

        if cleaned_tag and cleaned_tag not in cleaned_tags:
            cleaned_tags.append(cleaned_tag)

    return cleaned_tags


def detect_issue_type(bug_report: BugReport, normalized_tags: list[str]) -> str:
    """Assign a simple issue type from keywords in the report and tags."""
    searchable_text = " ".join(
        [
            bug_report.title,
            bug_report.prompt,
            bug_report.expected_behavior,
            bug_report.actual_behavior,
            " ".join(normalized_tags),
        ]
    ).lower()

    if "ignore" in searchable_text or "instruction" in searchable_text:
        return "instruction-following"

    if "format" in searchable_text or "json" in searchable_text or "bullet" in searchable_text:
        return "formatting"

    if "hallucin" in searchable_text:
        return "hallucination"

    return "general"


def build_summary(title: str, model_name: str, issue_type: str) -> str:
    readable_issue_type = issue_type.replace("-", " ")
    return f"{model_name} issue ({readable_issue_type}): {title}"


def normalize_bug_report(bug_report: BugReport) -> NormalizedIncident:
    """Convert a raw bug report into a normalized incident record."""
    normalized_title = normalize_text(bug_report.title)
    normalized_model_name = normalize_text(bug_report.model_name)
    normalized_prompt = normalize_text(bug_report.prompt)
    normalized_expected_behavior = normalize_text(bug_report.expected_behavior)
    normalized_actual_behavior = normalize_text(bug_report.actual_behavior)
    normalized_tags = normalize_tags(bug_report.tags)
    issue_type = detect_issue_type(bug_report, normalized_tags)
    summary = build_summary(normalized_title, normalized_model_name, issue_type)

    return NormalizedIncident(
        title=normalized_title,
        model_name=normalized_model_name,
        prompt_text=normalized_prompt,
        expected_behavior=normalized_expected_behavior,
        actual_behavior=normalized_actual_behavior,
        issue_type=issue_type,
        summary=summary,
        tags=normalized_tags,
    )
