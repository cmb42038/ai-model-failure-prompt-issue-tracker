from fastapi.testclient import TestClient

from app.main import app
from app.normalization import normalize_bug_report
from app.schemas import BugReport

client = TestClient(app)


def test_normalize_bug_report_cleans_fields() -> None:
    bug_report = BugReport(
        title="  Model ignored system instruction  ",
        model_name=" GPT-4.1-mini ",
        prompt="  Return JSON only.  ",
        expected_behavior="  Return valid JSON. ",
        actual_behavior=" Returned bullet points instead.  ",
        tags=[" Formatting ", "instruction following", "Formatting"],
    )

    normalized_incident = normalize_bug_report(bug_report)

    assert normalized_incident.title == "Model ignored system instruction"
    assert normalized_incident.model_name == "GPT-4.1-mini"
    assert normalized_incident.prompt_text == "Return JSON only."
    assert normalized_incident.expected_behavior == "Return valid JSON."
    assert normalized_incident.actual_behavior == "Returned bullet points instead."
    assert normalized_incident.issue_type == "instruction-following"
    assert normalized_incident.summary == (
        "GPT-4.1-mini issue (instruction following): Model ignored system "
        "instruction"
    )
    assert normalized_incident.tags == ["formatting", "instruction-following"]


def test_normalize_bug_report_endpoint_returns_normalized_incident() -> None:
    payload = {
        "title": "Response format drift",
        "model_name": "gpt-4.1-mini",
        "prompt": "Return JSON with one key named summary.",
        "expected_behavior": "Return valid JSON.",
        "actual_behavior": "Returned plain text paragraphs.",
        "tags": [" Formatting ", "JSON "],
    }

    response = client.post("/bug-reports/normalize", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "title": "Response format drift",
        "model_name": "gpt-4.1-mini",
        "prompt_text": "Return JSON with one key named summary.",
        "expected_behavior": "Return valid JSON.",
        "actual_behavior": "Returned plain text paragraphs.",
        "issue_type": "formatting",
        "summary": "gpt-4.1-mini issue (formatting): Response format drift",
        "tags": ["formatting", "json"],
    }
