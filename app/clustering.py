"""Baseline helpers for grouping similar incidents into rough clusters."""

from collections import Counter

from app.retrieval import build_tfidf_vectors, cosine_similarity, incident_to_text
from app.schemas import IncidentCluster, NormalizedIncident


def build_cluster_label(incidents: list[NormalizedIncident]) -> str:
    issue_types = [incident.issue_type for incident in incidents]
    most_common_issue_type = Counter(issue_types).most_common(1)[0][0]
    readable_issue_type = most_common_issue_type.replace("-", " ")
    return f"{readable_issue_type} patterns"


def cluster_incidents(
    incidents: list[NormalizedIncident],
    similarity_threshold: float = 0.25,
) -> list[IncidentCluster]:
    """Cluster incidents by connecting pairs above a similarity threshold."""
    if not incidents:
        return []

    documents = [incident_to_text(incident) for incident in incidents]
    vectors = build_tfidf_vectors(documents)
    connected_incidents: dict[int, set[int]] = {
        index: set() for index in range(len(incidents))
    }

    # Link incidents that are close enough in text space, then turn those
    # links into connected groups.
    for left_index in range(len(incidents)):
        for right_index in range(left_index + 1, len(incidents)):
            score = cosine_similarity(vectors[left_index], vectors[right_index])

            if score >= similarity_threshold:
                connected_incidents[left_index].add(right_index)
                connected_incidents[right_index].add(left_index)

    grouped_indices: list[list[int]] = []
    visited_indices: set[int] = set()

    for start_index in range(len(incidents)):
        if start_index in visited_indices:
            continue

        stack = [start_index]
        component: list[int] = []
        visited_indices.add(start_index)

        while stack:
            current_index = stack.pop()
            component.append(current_index)

            for neighbor_index in connected_incidents[current_index]:
                if neighbor_index not in visited_indices:
                    visited_indices.add(neighbor_index)
                    stack.append(neighbor_index)

        grouped_indices.append(sorted(component))

    grouped_indices.sort(key=lambda group: (-len(group), group[0]))
    clusters: list[IncidentCluster] = []

    for cluster_id, group in enumerate(grouped_indices, start=1):
        cluster_incidents_list = [incidents[index] for index in group]
        clusters.append(
            IncidentCluster(
                cluster_id=cluster_id,
                label=build_cluster_label(cluster_incidents_list),
                incident_count=len(cluster_incidents_list),
                incidents=cluster_incidents_list,
            )
        )

    return clusters
