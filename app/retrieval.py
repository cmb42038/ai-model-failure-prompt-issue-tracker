"""Baseline TF-IDF retrieval helpers for similar-incident search."""

import json
import math
import re
from collections import Counter
from pathlib import Path

from app.normalization import normalize_bug_report
from app.schemas import (
    BugReport,
    NormalizedIncident,
    SimilarIncidentMatch,
)

SAMPLE_INCIDENTS_PATH = Path(__file__).resolve().parent / "data" / "sample_incidents.json"


def load_sample_incidents() -> list[NormalizedIncident]:
    """Load the small sample incident corpus used by retrieval and demos."""
    with SAMPLE_INCIDENTS_PATH.open(encoding="utf-8") as file:
        raw_incidents = json.load(file)

    return [NormalizedIncident(**incident) for incident in raw_incidents]


def build_search_corpus(stored_bug_reports: list[BugReport]) -> list[NormalizedIncident]:
    """Combine sample incidents with the current in-memory raw reports."""
    incidents = load_sample_incidents()
    incidents.extend(normalize_bug_report(report) for report in stored_bug_reports)
    return incidents


def incident_to_text(incident: NormalizedIncident) -> str:
    return " ".join(
        [
            incident.title,
            incident.model_name,
            incident.prompt_text,
            incident.expected_behavior,
            incident.actual_behavior,
            incident.issue_type,
            incident.summary,
            " ".join(incident.tags),
        ]
    )


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9-]+", text.lower())


def build_tfidf_vectors(documents: list[str]) -> list[dict[str, float]]:
    tokenized_documents = [tokenize(document) for document in documents]
    document_count = len(tokenized_documents)
    document_frequencies: Counter[str] = Counter()

    for tokens in tokenized_documents:
        for token in set(tokens):
            document_frequencies[token] += 1

    vectors: list[dict[str, float]] = []

    for tokens in tokenized_documents:
        if not tokens:
            vectors.append({})
            continue

        term_counts = Counter(tokens)
        total_terms = len(tokens)
        vector: dict[str, float] = {}

        for token, count in term_counts.items():
            term_frequency = count / total_terms
            inverse_document_frequency = (
                math.log((1 + document_count) / (1 + document_frequencies[token])) + 1
            )
            vector[token] = term_frequency * inverse_document_frequency

        vectors.append(vector)

    return vectors


def cosine_similarity(left_vector: dict[str, float], right_vector: dict[str, float]) -> float:
    if not left_vector or not right_vector:
        return 0.0

    dot_product = sum(
        left_vector.get(token, 0.0) * right_vector.get(token, 0.0)
        for token in left_vector
    )
    left_size = math.sqrt(sum(value * value for value in left_vector.values()))
    right_size = math.sqrt(sum(value * value for value in right_vector.values()))

    if left_size == 0 or right_size == 0:
        return 0.0

    return dot_product / (left_size * right_size)


def find_similar_incidents(
    query_incident: NormalizedIncident,
    incidents: list[NormalizedIncident],
    top_k: int = 3,
) -> list[SimilarIncidentMatch]:
    """Return the top TF-IDF matches for a normalized incident."""
    if not incidents:
        return []

    documents = [incident_to_text(query_incident)]
    documents.extend(incident_to_text(incident) for incident in incidents)
    vectors = build_tfidf_vectors(documents)
    query_vector = vectors[0]
    incident_vectors = vectors[1:]
    matches: list[SimilarIncidentMatch] = []

    for incident, incident_vector in zip(incidents, incident_vectors):
        score = cosine_similarity(query_vector, incident_vector)
        matches.append(
            SimilarIncidentMatch(
                score=round(score, 4),
                incident=incident,
            )
        )

    matches.sort(key=lambda match: match.score, reverse=True)
    return matches[:top_k]
