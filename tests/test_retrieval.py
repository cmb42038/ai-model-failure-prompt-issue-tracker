import pytest
from fastapi.testclient import TestClient

from app.main import app, bug_reports
from app.normalization import normalize_bug_report
from app.retrieval import build_search_corpus, find_similar_incidents
from app.schemas import BugReport

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_bug_reports() -> None:
    bug_reports.clear()


def test_find_similar_incidents_returns_best_sample_match() -> None:
    query_report = BugReport(
        title="JSON output came back as plain text",
        model_name="gpt-4.1-mini",
        prompt="Return valid JSON with one summary key.",
        expected_behavior="Return valid JSON only.",
        actual_behavior="Returned plain text instead of JSON.",
        tags=["formatting", "json"],
    )

    query_incident = normalize_bug_report(query_report)
    incidents = build_search_corpus([])
    matches = find_similar_incidents(query_incident, incidents)

    assert matches[0].incident.title == "JSON response returned as plain text"
    assert matches[0].incident.issue_type == "formatting"
    assert matches[0].score > 0


def test_similar_incidents_endpoint_returns_top_matches() -> None:
    stored_payload = {
        "title": "Model ignored system instruction",
        "model_name": "gpt-4.1-mini",
        "prompt": "Summarize this support ticket in one sentence.",
        "expected_behavior": "Return a one-sentence summary.",
        "actual_behavior": "Returned a long bulleted list instead.",
        "tags": ["formatting", "instruction-following"],
    }

    client.post("/bug-reports", json=stored_payload)
    response = client.post("/incidents/similar", json=stored_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["query_incident"]["issue_type"] == "instruction-following"
    assert len(data["matches"]) == 3
    assert data["matches"][0]["incident"]["title"] == "Model ignored system instruction"
    assert data["matches"][0]["score"] >= data["matches"][1]["score"]
