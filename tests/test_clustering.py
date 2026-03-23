import pytest
from fastapi.testclient import TestClient

from app.clustering import cluster_incidents
from app.main import app, bug_reports
from app.schemas import NormalizedIncident

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_bug_reports() -> None:
    bug_reports.clear()


def test_cluster_incidents_groups_related_incidents() -> None:
    incidents = [
        NormalizedIncident(
            title="JSON answer returned as plain text",
            model_name="gpt-4.1-mini",
            prompt_text="Return valid JSON with a summary key.",
            expected_behavior="Return valid JSON only.",
            actual_behavior="Returned plain text instead of JSON.",
            issue_type="formatting",
            summary="gpt-4.1-mini issue (formatting): JSON answer returned as plain text",
            tags=["formatting", "json"],
        ),
        NormalizedIncident(
            title="JSON output came back as bullet points",
            model_name="gpt-4.1",
            prompt_text="Return valid JSON with one summary field.",
            expected_behavior="Return valid JSON with one summary field.",
            actual_behavior="Returned bullet points instead of JSON.",
            issue_type="formatting",
            summary="gpt-4.1 issue (formatting): JSON output came back as bullet points",
            tags=["formatting", "json"],
        ),
        NormalizedIncident(
            title="Catalog answer hallucinated a fake feature",
            model_name="gpt-4.1-mini",
            prompt_text="Use only the provided catalog.",
            expected_behavior="Use only the provided catalog details.",
            actual_behavior="Invented a product feature that was not provided.",
            issue_type="hallucination",
            summary="gpt-4.1-mini issue (hallucination): Catalog answer hallucinated a fake feature",
            tags=["hallucination", "factuality"],
        ),
    ]

    clusters = cluster_incidents(incidents, similarity_threshold=0.2)

    assert len(clusters) == 2
    assert clusters[0].label == "formatting patterns"
    assert clusters[0].incident_count == 2
    assert clusters[1].label == "hallucination patterns"
    assert clusters[1].incident_count == 1


def test_incidents_clusters_endpoint_returns_baseline_groups() -> None:
    stored_payload = {
        "title": "JSON response returned as plain text",
        "model_name": "gpt-4.1-mini",
        "prompt": "Return valid JSON with a summary field.",
        "expected_behavior": "Return valid JSON only.",
        "actual_behavior": "Returned plain text paragraphs instead of JSON.",
        "tags": ["formatting", "json"],
    }

    client.post("/bug-reports", json=stored_payload)
    response = client.get("/incidents/clusters")

    assert response.status_code == 200
    data = response.json()

    assert data["method"] == "baseline-tfidf-threshold-clustering"
    assert data["total_incidents"] == 6
    assert data["total_clusters"] >= 3
    assert data["clusters"][0]["incident_count"] >= 2
