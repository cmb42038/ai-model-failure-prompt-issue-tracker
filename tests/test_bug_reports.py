import pytest
from fastapi.testclient import TestClient

from app.main import app, bug_reports

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_bug_reports() -> None:
    bug_reports.clear()


def test_create_bug_report() -> None:
    payload = {
        "title": "Model ignored system instruction",
        "model_name": "gpt-4.1-mini",
        "prompt": "Summarize this support ticket in one sentence.",
        "expected_behavior": "Return a one-sentence summary.",
        "actual_behavior": "Returned a long bulleted list instead.",
        "tags": ["formatting", "instruction-following"],
    }

    response = client.post("/bug-reports", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Bug report stored",
        "bug_report": payload,
        "total_reports": 1,
    }
    assert len(bug_reports) == 1


def test_create_bug_report_requires_required_fields() -> None:
    payload = {
        "model_name": "gpt-4.1-mini",
        "prompt": "Summarize this support ticket in one sentence.",
        "expected_behavior": "Return a one-sentence summary.",
        "actual_behavior": "Returned a long bulleted list instead.",
    }

    response = client.post("/bug-reports", json=payload)

    assert response.status_code == 422
    assert bug_reports == []
