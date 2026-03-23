"""Small baseline benchmark helpers for the current project features."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.clustering import cluster_incidents
from app.normalization import normalize_bug_report
from app.repro import build_fallback_repro_case_draft
from app.retrieval import find_similar_incidents, load_sample_incidents
from app.schemas import BugReport, NormalizedIncident

EVALUATION_CASES_PATH = Path(__file__).resolve().parent / "data" / "evaluation_cases.json"


class EvaluationCase(BaseModel):
    case_id: str
    bug_report: BugReport
    expected_normalized_title: str
    expected_issue_type: str
    expected_top_match_title: str
    expected_cluster_group: str


def load_evaluation_cases() -> list[EvaluationCase]:
    """Load the labeled benchmark cases used by the evaluation module."""
    with EVALUATION_CASES_PATH.open(encoding="utf-8") as file:
        raw_cases = json.load(file)

    return [EvaluationCase(**case) for case in raw_cases]


def score_rate(passed: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(passed / total, 2)


def has_text(value: str) -> bool:
    return bool(value and value.strip())


def incident_key(incident: NormalizedIncident) -> tuple[str, str, str]:
    return (incident.title, incident.model_name, incident.summary)


def evaluate_normalization(cases: list[EvaluationCase]) -> dict[str, Any]:
    structure_passed = 0
    title_matches = 0
    issue_type_matches = 0
    failed_cases: list[dict[str, str]] = []

    for case in cases:
        incident = normalize_bug_report(case.bug_report)
        structure_ok = all(
            [
                has_text(incident.title),
                has_text(incident.model_name),
                has_text(incident.prompt_text),
                has_text(incident.expected_behavior),
                has_text(incident.actual_behavior),
                has_text(incident.issue_type),
                has_text(incident.summary),
                isinstance(incident.tags, list),
            ]
        )
        title_ok = incident.title == case.expected_normalized_title
        issue_type_ok = incident.issue_type == case.expected_issue_type

        if structure_ok:
            structure_passed += 1

        if title_ok:
            title_matches += 1

        if issue_type_ok:
            issue_type_matches += 1

        if not (structure_ok and title_ok and issue_type_ok):
            failed_cases.append(
                {
                    "case_id": case.case_id,
                    "actual_title": incident.title,
                    "actual_issue_type": incident.issue_type,
                }
            )

    return {
        "total_cases": len(cases),
        "structure_passed": structure_passed,
        "structure_rate": score_rate(structure_passed, len(cases)),
        "title_matches": title_matches,
        "title_match_rate": score_rate(title_matches, len(cases)),
        "issue_type_matches": issue_type_matches,
        "issue_type_match_rate": score_rate(issue_type_matches, len(cases)),
        "failed_cases": failed_cases,
    }


def evaluate_retrieval(cases: list[EvaluationCase]) -> dict[str, Any]:
    sample_incidents = load_sample_incidents()
    top_1_hits = 0
    failed_cases: list[dict[str, str]] = []

    for case in cases:
        query_incident = normalize_bug_report(case.bug_report)
        matches = find_similar_incidents(query_incident, sample_incidents, top_k=1)
        top_match_title = matches[0].incident.title if matches else "no match"

        if top_match_title == case.expected_top_match_title:
            top_1_hits += 1
        else:
            failed_cases.append(
                {
                    "case_id": case.case_id,
                    "expected_top_match_title": case.expected_top_match_title,
                    "actual_top_match_title": top_match_title,
                }
            )

    return {
        "total_cases": len(cases),
        "top_1_hits": top_1_hits,
        "top_1_accuracy": score_rate(top_1_hits, len(cases)),
        "failed_cases": failed_cases,
    }


def evaluate_clustering(cases: list[EvaluationCase]) -> dict[str, Any]:
    normalized_incidents_by_case = {
        case.case_id: normalize_bug_report(case.bug_report) for case in cases
    }
    clusters = cluster_incidents(list(normalized_incidents_by_case.values()))
    case_id_by_incident_key = {
        incident_key(incident): case_id
        for case_id, incident in normalized_incidents_by_case.items()
    }
    cluster_by_case_id: dict[str, int] = {}

    for cluster in clusters:
        for incident in cluster.incidents:
            cluster_by_case_id[case_id_by_incident_key[incident_key(incident)]] = (
                cluster.cluster_id
            )

    pairwise_checks = 0
    pairwise_correct = 0
    failed_pairs: list[dict[str, str | bool]] = []

    for left_index in range(len(cases)):
        for right_index in range(left_index + 1, len(cases)):
            left_case = cases[left_index]
            right_case = cases[right_index]
            expected_same_group = (
                left_case.expected_cluster_group == right_case.expected_cluster_group
            )
            predicted_same_group = (
                cluster_by_case_id[left_case.case_id]
                == cluster_by_case_id[right_case.case_id]
            )
            pairwise_checks += 1

            if expected_same_group == predicted_same_group:
                pairwise_correct += 1
            else:
                failed_pairs.append(
                    {
                        "left_case_id": left_case.case_id,
                        "right_case_id": right_case.case_id,
                        "expected_same_group": expected_same_group,
                        "predicted_same_group": predicted_same_group,
                    }
                )

    return {
        "total_cases": len(cases),
        "total_clusters": len(clusters),
        "pairwise_checks": pairwise_checks,
        "pairwise_correct": pairwise_correct,
        "pairwise_accuracy": score_rate(pairwise_correct, pairwise_checks),
        "clusters": [
            {
                "cluster_id": cluster.cluster_id,
                "label": cluster.label,
                "incident_titles": [incident.title for incident in cluster.incidents],
            }
            for cluster in clusters
        ],
        "failed_pairs": failed_pairs,
    }


def evaluate_repro_drafting(cases: list[EvaluationCase]) -> dict[str, Any]:
    complete_drafts = 0
    likely_failure_type_matches = 0
    failed_cases: list[dict[str, str]] = []

    for case in cases:
        incident = normalize_bug_report(case.bug_report)
        draft = build_fallback_repro_case_draft(incident)
        complete_draft = all(
            [
                has_text(draft.summary),
                has_text(draft.likely_failure_type),
                bool(draft.reproduction_steps),
                all(has_text(step) for step in draft.reproduction_steps),
                has_text(draft.expected_behavior),
                has_text(draft.actual_behavior),
                has_text(draft.test_case_draft.title),
                has_text(draft.test_case_draft.pass_condition),
                has_text(draft.test_case_draft.fail_condition),
            ]
        )
        likely_failure_type_ok = (
            draft.likely_failure_type == case.expected_issue_type.replace("-", " ")
        )

        if complete_draft:
            complete_drafts += 1

        if likely_failure_type_ok:
            likely_failure_type_matches += 1

        if not (complete_draft and likely_failure_type_ok):
            failed_cases.append(
                {
                    "case_id": case.case_id,
                    "actual_likely_failure_type": draft.likely_failure_type,
                }
            )

    return {
        "mode": "fallback",
        "total_cases": len(cases),
        "complete_drafts": complete_drafts,
        "completeness_rate": score_rate(complete_drafts, len(cases)),
        "likely_failure_type_matches": likely_failure_type_matches,
        "likely_failure_type_match_rate": score_rate(
            likely_failure_type_matches, len(cases)
        ),
        "failed_cases": failed_cases,
    }


def run_evaluation() -> dict[str, Any]:
    """Run the small baseline benchmark and return a JSON-friendly report."""
    cases = load_evaluation_cases()

    return {
        "benchmark_name": "baseline-evaluation",
        "dataset_path": str(EVALUATION_CASES_PATH),
        "total_cases": len(cases),
        "normalization": evaluate_normalization(cases),
        "retrieval": evaluate_retrieval(cases),
        "clustering": evaluate_clustering(cases),
        "repro_drafting": evaluate_repro_drafting(cases),
        "limitations": [
            "The benchmark dataset is small and hand-written.",
            "Normalization scoring checks structure, cleaned titles, and issue-type labels only.",
            "Retrieval scoring uses a simple top-1 match against the sample incident dataset.",
            "Clustering scoring uses pairwise group agreement instead of a full clustering metric.",
            "Repro drafting scoring checks fallback draft completeness, not writing quality or live API behavior.",
        ],
    }


def main() -> None:
    report = run_evaluation()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
