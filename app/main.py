from typing import Any

from fastapi import FastAPI

from app.clustering import cluster_incidents
from app.normalization import normalize_bug_report
from app.retrieval import build_search_corpus, find_similar_incidents
from app.schemas import (
    BugReport,
    IncidentClustersResponse,
    NormalizedIncident,
    SimilarIncidentsResponse,
)

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


@app.post("/incidents/similar", response_model=SimilarIncidentsResponse)
def find_similar_incidents_endpoint(
    bug_report: BugReport,
) -> SimilarIncidentsResponse:
    query_incident = normalize_bug_report(bug_report)
    incidents = build_search_corpus(bug_reports)
    matches = find_similar_incidents(query_incident, incidents)

    return SimilarIncidentsResponse(
        query_incident=query_incident,
        matches=matches,
    )


@app.get("/incidents/clusters", response_model=IncidentClustersResponse)
def cluster_incidents_endpoint() -> IncidentClustersResponse:
    incidents = build_search_corpus(bug_reports)
    clusters = cluster_incidents(incidents)

    return IncidentClustersResponse(
        method="baseline-tfidf-threshold-clustering",
        total_incidents=len(incidents),
        total_clusters=len(clusters),
        clusters=clusters,
    )
