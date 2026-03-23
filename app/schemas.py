from pydantic import BaseModel, Field


class BugReport(BaseModel):
    title: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    expected_behavior: str = Field(min_length=1)
    actual_behavior: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class NormalizedIncident(BaseModel):
    title: str
    model_name: str
    prompt_text: str
    expected_behavior: str
    actual_behavior: str
    issue_type: str
    summary: str
    tags: list[str] = Field(default_factory=list)


class SimilarIncidentMatch(BaseModel):
    score: float
    incident: NormalizedIncident


class SimilarIncidentsResponse(BaseModel):
    query_incident: NormalizedIncident
    matches: list[SimilarIncidentMatch] = Field(default_factory=list)


class IncidentCluster(BaseModel):
    cluster_id: int
    label: str
    incident_count: int
    incidents: list[NormalizedIncident] = Field(default_factory=list)


class IncidentClustersResponse(BaseModel):
    method: str
    total_incidents: int
    total_clusters: int
    clusters: list[IncidentCluster] = Field(default_factory=list)
