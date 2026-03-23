"""Helpers for repro-case drafting with a fallback and an optional LLM path."""

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, request

from dotenv import load_dotenv
from pydantic import ValidationError

from app.normalization import normalize_bug_report
from app.schemas import (
    BugReport,
    NormalizedIncident,
    PassFailTestCaseDraft,
    ReproCaseDraft,
)

load_dotenv()


@dataclass
class ReproLLMConfig:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: int


def is_llm_enabled() -> bool:
    enabled_value = os.getenv("REPRO_USE_LLM", "false").lower()
    return enabled_value in {"1", "true", "yes"}


def get_repro_llm_config() -> ReproLLMConfig | None:
    """Load optional repro-drafting LLM settings from environment variables."""
    if not is_llm_enabled():
        return None

    api_key = os.getenv("REPRO_LLM_API_KEY")
    model = os.getenv("REPRO_LLM_MODEL")

    if not api_key or not model:
        return None

    return ReproLLMConfig(
        api_key=api_key,
        model=model,
        base_url=os.getenv("REPRO_LLM_BASE_URL", "https://api.openai.com/v1"),
        timeout_seconds=int(os.getenv("REPRO_LLM_TIMEOUT_SECONDS", "30")),
    )


def build_repro_system_prompt() -> str:
    """Build the system prompt used by the optional LLM path."""
    return (
        "You draft concise AI bug reproduction cases. "
        "Return JSON only with these fields: "
        "summary, likely_failure_type, reproduction_steps, expected_behavior, "
        "actual_behavior, test_case_draft. "
        "test_case_draft must include title, pass_condition, and fail_condition."
    )


def build_repro_user_prompt(incident: NormalizedIncident) -> str:
    """Build the user prompt from a normalized incident."""
    return f"""
Draft a reproduction case for this normalized AI incident.

Title: {incident.title}
Model: {incident.model_name}
Prompt: {incident.prompt_text}
Expected behavior: {incident.expected_behavior}
Actual behavior: {incident.actual_behavior}
Issue type: {incident.issue_type}
Summary: {incident.summary}
Tags: {", ".join(incident.tags) or "none"}

Keep the reproduction steps short and concrete.
""".strip()


def strip_code_fences(value: str) -> str:
    cleaned_value = value.strip()

    if cleaned_value.startswith("```"):
        lines = cleaned_value.splitlines()
        cleaned_value = "\n".join(lines[1:-1]).strip()

    return cleaned_value


def parse_repro_case_response(response_text: str) -> ReproCaseDraft:
    """Parse JSON returned by an LLM into the repro draft schema."""
    cleaned_text = strip_code_fences(response_text)
    payload = json.loads(cleaned_text)
    return ReproCaseDraft(**payload)


def call_openai_compatible_api(
    system_prompt: str,
    user_prompt: str,
    config: ReproLLMConfig,
) -> str:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    api_request = request.Request(
        url=f"{config.base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with request.urlopen(api_request, timeout=config.timeout_seconds) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    content = response_payload["choices"][0]["message"]["content"]

    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "".join(text_parts)

    return str(content)


def build_fallback_repro_case_draft(incident: NormalizedIncident) -> ReproCaseDraft:
    """Create a deterministic local repro draft when no LLM is in use."""
    readable_failure_type = incident.issue_type.replace("-", " ")

    return ReproCaseDraft(
        summary=incident.summary,
        likely_failure_type=readable_failure_type,
        reproduction_steps=[
            f"Use the model {incident.model_name}.",
            f"Send this prompt to the model: {incident.prompt_text}",
            "Capture the full model response.",
            f"Compare the response against this expectation: {incident.expected_behavior}",
        ],
        expected_behavior=incident.expected_behavior,
        actual_behavior=incident.actual_behavior,
        test_case_draft=PassFailTestCaseDraft(
            title=f"Check {readable_failure_type} behavior for {incident.title}",
            pass_condition=(
                "Pass if the response matches the expected behavior: "
                f"{incident.expected_behavior}"
            ),
            fail_condition=(
                "Fail if the response matches the observed issue: "
                f"{incident.actual_behavior}"
            ),
        ),
    )


def generate_repro_case_draft_from_incident(
    incident: NormalizedIncident,
    api_caller: Callable[[str, str, ReproLLMConfig], str] = call_openai_compatible_api,
) -> ReproCaseDraft:
    """Generate a repro draft from a normalized incident."""
    config = get_repro_llm_config()

    if config is None:
        return build_fallback_repro_case_draft(incident)

    system_prompt = build_repro_system_prompt()
    user_prompt = build_repro_user_prompt(incident)

    try:
        response_text = api_caller(system_prompt, user_prompt, config)
        return parse_repro_case_response(response_text)
    except (KeyError, TypeError, ValueError, ValidationError, error.URLError, OSError):
        return build_fallback_repro_case_draft(incident)


def generate_repro_case_draft_from_bug_report(
    bug_report: BugReport,
    api_caller: Callable[[str, str, ReproLLMConfig], str] = call_openai_compatible_api,
) -> ReproCaseDraft:
    """Generate a repro draft from a raw bug report."""
    incident = normalize_bug_report(bug_report)
    return generate_repro_case_draft_from_incident(incident, api_caller=api_caller)
