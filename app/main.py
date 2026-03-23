from typing import Any

from fastapi import FastAPI

from app.normalization import normalize_bug_report
from app.schemas import BugReport, NormalizedIncident

app = FastAPI(title="AI Model Failure / Prompt Issue Tracker")
bug_reports: list[BugReport] = []


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "project": "AI Model Failure / Prompt Issue Tracker",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/bug-reports")
def create_bug_report(bug_report: BugReport) -> dict[str, Any]:
    bug_reports.append(bug_report)

    return {
        "message": "Bug report stored",
        "bug_report": bug_report.model_dump(),
        "total_reports": len(bug_reports),
    }


@app.post("/bug-reports/normalize", response_model=NormalizedIncident)
def normalize_bug_report_endpoint(bug_report: BugReport) -> NormalizedIncident:
    return normalize_bug_report(bug_report)
