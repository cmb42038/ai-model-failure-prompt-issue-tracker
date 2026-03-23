from app.evaluation import load_evaluation_cases, run_evaluation


def test_load_evaluation_cases() -> None:
    cases = load_evaluation_cases()

    assert len(cases) == 5
    assert cases[0].case_id == "formatting_plain_text"
    assert cases[-1].expected_issue_type == "hallucination"


def test_run_evaluation_returns_expected_sections() -> None:
    report = run_evaluation()

    assert report["benchmark_name"] == "baseline-evaluation"
    assert report["total_cases"] == 5
    assert report["normalization"]["total_cases"] == 5
    assert report["retrieval"]["total_cases"] == 5
    assert report["clustering"]["total_cases"] == 5
    assert report["repro_drafting"]["mode"] == "fallback"
    assert len(report["limitations"]) == 5
    assert 0.0 <= report["clustering"]["pairwise_accuracy"] <= 1.0
