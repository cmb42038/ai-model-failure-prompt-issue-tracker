import pytest
from fastapi.testclient import TestClient

from app.main import app, bug_reports
from app.repro import (
    build_fallback_repro_case_draft,
    build_repro_user_prompt,
    generate_repro_case_draft_from_incident,
    get_repro_llm_config,
    parse_repro_case_response,
)
from app.schemas import NormalizedIncident

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_bug_reports() -> None:
    bug_reports.clear()


def build_sample_incident() -> NormalizedIncident:
    return NormalizedIncident(
        title="JSON response returned as plain text",
        model_name="gpt-4.1-mini",
        prompt_text="Return valid JSON with a summary field.",
        expected_behavior="Return valid JSON only.",
        actual_behavior="Returned plain text paragraphs instead of JSON.",
        issue_type="formatting",
        summary="gpt-4.1-mini issue (formatting): JSON response returned as plain text",
        tags=["formatting", "json"],
    )


def test_build_fallback_repro_case_draft() -> None:
    incident = build_sample_incident()

    repro_case_draft = build_fallback_repro_case_draft(incident)

    assert repro_case_draft.summary == incident.summary
    assert repro_case_draft.likely_failure_type == "formatting"
    assert len(repro_case_draft.reproduction_steps) == 4
    assert repro_case_draft.test_case_draft.title.startswith("Check formatting behavior")


def test_build_repro_user_prompt_includes_incident_fields() -> None:
    incident = build_sample_incident()

    prompt = build_repro_user_prompt(incident)

    assert "Title: JSON response returned as plain text" in prompt
    assert "Model: gpt-4.1-mini" in prompt
    assert "Issue type: formatting" in prompt


def test_parse_repro_case_response_supports_code_fences() -> None:
    response_text = """
```json
{
  "summary": "Formatting issue while requesting JSON output.",
  "likely_failure_type": "formatting",
  "reproduction_steps": [
    "Use the model gpt-4.1-mini.",
    "Send the prompt requesting JSON output."
  ],
  "expected_behavior": "Return valid JSON only.",
  "actual_behavior": "Returned plain text instead of JSON.",
  "test_case_draft": {
    "title": "Check JSON output formatting",
    "pass_condition": "Pass if the output is valid JSON.",
    "fail_condition": "Fail if the output is plain text."
  }
}
```
""".strip()

    repro_case_draft = parse_repro_case_response(response_text)

    assert repro_case_draft.likely_failure_type == "formatting"
    assert repro_case_draft.test_case_draft.fail_condition == (
        "Fail if the output is plain text."
    )


def test_get_repro_llm_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPRO_USE_LLM", "true")
    monkeypatch.setenv("REPRO_LLM_API_KEY", "test-key")
    monkeypatch.setenv("REPRO_LLM_MODEL", "test-model")
    monkeypatch.setenv("REPRO_LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("REPRO_LLM_TIMEOUT_SECONDS", "12")

    config = get_repro_llm_config()

    assert config is not None
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.base_url == "https://example.com/v1"
    assert config.timeout_seconds == 12


def test_generate_repro_case_draft_from_incident_falls_back_when_llm_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incident = build_sample_incident()
    monkeypatch.setenv("REPRO_USE_LLM", "false")

    repro_case_draft = generate_repro_case_draft_from_incident(incident)

    assert repro_case_draft.summary == incident.summary
    assert repro_case_draft.expected_behavior == incident.expected_behavior


def test_repro_draft_endpoint_returns_fallback_draft_without_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPRO_USE_LLM", "false")
    payload = {
        "title": "Model ignored system instruction",
        "model_name": "gpt-4.1-mini",
        "prompt": "Summarize this support ticket in one sentence.",
        "expected_behavior": "Return a one-sentence summary.",
        "actual_behavior": "Returned a long bulleted list instead.",
        "tags": ["formatting", "instruction-following"],
    }

    response = client.post("/bug-reports/repro-draft", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["likely_failure_type"] == "instruction following"
    assert len(data["reproduction_steps"]) == 4
    assert "pass_condition" in data["test_case_draft"]


def test_incident_repro_draft_endpoint_accepts_normalized_incident(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPRO_USE_LLM", "false")
    incident = build_sample_incident().model_dump()

    response = client.post("/incidents/repro-draft", json=incident)

    assert response.status_code == 200
    assert response.json()["summary"] == incident["summary"]
