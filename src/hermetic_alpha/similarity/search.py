"""Dependency-free nearest-neighbor search for numeric chart vectors."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from math import sqrt
from typing import Any, Literal

SimilarityMetric = Literal["cosine", "euclidean"]
ReportScalar = str | int | float | bool | date | datetime | None


@dataclass(frozen=True)
class SimilarityCandidate:
    """A caller-owned vector plus an ID and optional payload."""

    id: str
    vector: Sequence[float]
    payload: Any = None


@dataclass(frozen=True)
class NearestNeighbor:
    """A ranked nearest-neighbor search result."""

    id: str
    score: float
    distance: float
    payload: Any = None


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity for two same-length numeric vectors."""

    _validate_pair(left, right)
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("cosine similarity requires non-zero vectors")
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def euclidean_distance(left: Sequence[float], right: Sequence[float]) -> float:
    """Return Euclidean distance for two same-length numeric vectors."""

    _validate_pair(left, right)
    return sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


def find_nearest(
    query_vector: Sequence[float],
    candidates: Sequence[SimilarityCandidate],
    *,
    limit: int | None = None,
    metric: SimilarityMetric = "cosine",
) -> list[NearestNeighbor]:
    """Rank candidates nearest to ``query_vector``.

    Empty candidate sets return an empty list. Exact score ties are resolved by
    candidate ID so repeated runs with the same input return the same ordering.
    """

    if not query_vector:
        raise ValueError("query_vector must not be empty")
    if limit is not None and limit <= 0:
        raise ValueError("limit must be a positive integer")
    if metric not in ("cosine", "euclidean"):
        raise ValueError("metric must be 'cosine' or 'euclidean'")

    neighbors = [
        _rank_candidate(query_vector, candidate, metric)
        for candidate in candidates
    ]
    if metric == "cosine":
        neighbors.sort(key=lambda neighbor: (-neighbor.score, neighbor.distance, neighbor.id))
    else:
        neighbors.sort(key=lambda neighbor: (neighbor.distance, neighbor.id))
    return neighbors[:limit]


def nearest_neighbor_rows(
    results: Sequence[NearestNeighbor],
    *,
    payload_fields: Sequence[str] | None = None,
) -> list[dict[str, ReportScalar]]:
    """Return flat CSV-compatible rows for ranked nearest-neighbor results.

    Scalar payloads are emitted in a ``payload`` column. Mapping payloads are
    included only through explicitly requested ``payload_fields`` and nested
    selected values are rejected so report schemas stay inspectable.
    """

    validated_payload_fields = _validate_payload_fields(payload_fields)
    rows: list[dict[str, ReportScalar]] = []
    for rank, result in enumerate(_validated_nearest_neighbors(results), start=1):
        row: dict[str, ReportScalar] = {
            "rank": rank,
            "id": result.id,
            "score": result.score,
            "distance": result.distance,
        }
        _add_payload_fields(row, result.payload, validated_payload_fields)
        rows.append(row)
    return rows


def nearest_neighbor_group_rows(
    searches: Mapping[str, Sequence[NearestNeighbor]] | Sequence[tuple[str, Sequence[NearestNeighbor]]],
    *,
    payload_fields: Sequence[str] | None = None,
) -> list[dict[str, ReportScalar]]:
    """Return ordered flat ranked-neighbor rows for several declared searches."""

    rows: list[dict[str, ReportScalar]] = []
    seen_search_ids: set[str] = set()
    for search_id, results in _iter_named_searches(searches):
        _validate_search_id(search_id, "search ID")
        if search_id in seen_search_ids:
            raise ValueError("search IDs must be unique")
        seen_search_ids.add(search_id)
        rows.extend(
            {
                "search_id": search_id,
                **row,
            }
            for row in nearest_neighbor_rows(results, payload_fields=payload_fields)
        )
    return rows


def nearest_neighbor_summary_row(
    results: Sequence[NearestNeighbor],
    *,
    query_id: str | None = None,
    metric: SimilarityMetric | None = None,
    limit: int | None = None,
) -> dict[str, ReportScalar]:
    """Return compact metadata for a nearest-neighbor search run."""

    result_values = _validated_nearest_neighbors(results)
    scores = [result.score for result in result_values]
    distances = [result.distance for result in result_values]
    top = result_values[0] if result_values else None

    return {
        "query_id": query_id,
        "metric": metric,
        "limit": limit,
        "result_count": len(result_values),
        "top_id": top.id if top is not None else None,
        "top_score": top.score if top is not None else None,
        "top_distance": top.distance if top is not None else None,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "min_distance": min(distances) if distances else None,
        "max_distance": max(distances) if distances else None,
    }


def nearest_neighbor_summary_rows(
    searches: Mapping[str, Sequence[NearestNeighbor]] | Sequence[tuple[str, Sequence[NearestNeighbor]]],
    *,
    query_ids: Mapping[str, str | None] | Sequence[tuple[str, str | None]] | None = None,
    metrics: Mapping[str, SimilarityMetric | None] | Sequence[tuple[str, SimilarityMetric | None]] | None = None,
    limits: Mapping[str, int | None] | Sequence[tuple[str, int | None]] | None = None,
) -> list[dict[str, ReportScalar]]:
    """Return ordered compact metadata rows for several nearest-neighbor searches."""

    named_searches = list(_iter_named_searches(searches))
    query_id_by_search = _optional_metadata_by_search(query_ids, "query ID")
    metric_by_search = _optional_metadata_by_search(metrics, "metric")
    limit_by_search = _optional_metadata_by_search(limits, "limit")
    rows: list[dict[str, ReportScalar]] = []
    seen_search_ids: set[str] = set()

    for search_id, results in named_searches:
        _validate_search_id(search_id, "search ID")
        if search_id in seen_search_ids:
            raise ValueError("search IDs must be unique")
        seen_search_ids.add(search_id)

    _reject_unknown_metadata_search_ids(query_id_by_search, seen_search_ids, "query ID")
    _reject_unknown_metadata_search_ids(metric_by_search, seen_search_ids, "metric")
    _reject_unknown_metadata_search_ids(limit_by_search, seen_search_ids, "limit")

    for search_id, results in named_searches:
        row = nearest_neighbor_summary_row(
            results,
            query_id=query_id_by_search.get(search_id),
            metric=metric_by_search.get(search_id),
            limit=limit_by_search.get(search_id),
        )
        rows.append({"search_id": search_id, **row})
    return rows


def _iter_named_searches(
    searches: Mapping[str, Sequence[NearestNeighbor]] | Sequence[tuple[str, Sequence[NearestNeighbor]]],
) -> Iterable[tuple[str, Sequence[NearestNeighbor]]]:
    if isinstance(searches, Mapping):
        yield from searches.items()
        return
    for index, entry in enumerate(searches):
        if isinstance(entry, str | bytes) or not isinstance(entry, Sequence) or len(entry) != 2:
            raise ValueError(
                f"named search entry {index} must be a two-item "
                "(search_id, results) pair"
            )
        search_id, results = entry
        yield search_id, results


def _validated_nearest_neighbors(results: Sequence[NearestNeighbor]) -> list[NearestNeighbor]:
    result_values: list[NearestNeighbor] = []
    for index, result in enumerate(results):
        if not isinstance(result, NearestNeighbor):
            raise ValueError(
                "nearest-neighbor results must contain NearestNeighbor values; "
                f"result at index {index} has type {type(result).__name__}"
            )
        result_values.append(result)
    return result_values


def _optional_metadata_by_search(
    values: Mapping[str, Any] | Sequence[tuple[str, Any]] | None,
    label: str,
) -> dict[str, Any]:
    if values is None:
        return {}

    metadata: dict[str, Any] = {}
    items = values.items() if isinstance(values, Mapping) else _iter_named_metadata(values, label)
    for search_id, value in items:
        _validate_search_id(search_id, f"{label} search ID")
        if search_id in metadata:
            raise ValueError(f"{label} search IDs must be unique")
        metadata[search_id] = value
    return metadata


def _iter_named_metadata(
    values: Sequence[tuple[str, Any]],
    label: str,
) -> Iterable[tuple[str, Any]]:
    for index, entry in enumerate(values):
        if isinstance(entry, str | bytes) or not isinstance(entry, Sequence) or len(entry) != 2:
            raise ValueError(
                f"{label} metadata entry {index} must be a two-item "
                "(search_id, value) pair"
            )
        search_id, value = entry
        yield search_id, value


def _validate_search_id(search_id: Any, label: str) -> None:
    if not isinstance(search_id, str):
        raise ValueError(f"{label} must be a string")
    if not search_id.strip():
        raise ValueError(f"{label} must not be blank")
    if search_id != search_id.strip():
        raise ValueError(f"{label} must not include leading or trailing whitespace")


def _reject_unknown_metadata_search_ids(
    metadata: Mapping[str, Any],
    declared_search_ids: set[str],
    label: str,
) -> None:
    unknown_ids = [search_id for search_id in metadata if search_id not in declared_search_ids]
    if unknown_ids:
        raise ValueError(f"{label} search IDs must match declared searches")


def _rank_candidate(
    query_vector: Sequence[float],
    candidate: SimilarityCandidate,
    metric: SimilarityMetric,
) -> NearestNeighbor:
    if metric == "cosine":
        score = cosine_similarity(query_vector, candidate.vector)
        distance = 1 - score
    else:
        distance = euclidean_distance(query_vector, candidate.vector)
        score = -distance
    return NearestNeighbor(
        id=candidate.id,
        score=score,
        distance=distance,
        payload=candidate.payload,
    )


def _add_payload_fields(
    row: dict[str, ReportScalar],
    payload: Any,
    payload_fields: Sequence[str] | None,
) -> None:
    if _is_report_scalar(payload):
        row["payload"] = payload
        return

    if payload_fields is None:
        return

    if not isinstance(payload, Mapping):
        raise TypeError("payload_fields requires mapping payload values")

    for field in payload_fields:
        value = payload.get(field)
        if not _is_report_scalar(value):
            raise TypeError(
                f"payload field {field!r} contains unsupported nested value {type(value).__name__}"
            )
        row[f"payload_{field}"] = value


def _validate_payload_fields(payload_fields: Sequence[str] | None) -> Sequence[str] | None:
    if payload_fields is None:
        return None
    for field in payload_fields:
        if not isinstance(field, str) or not field.strip():
            raise ValueError("payload field names must be non-blank strings")
    return payload_fields


def _is_report_scalar(value: Any) -> bool:
    return isinstance(value, str | int | float | bool | date | datetime) or value is None


def _validate_pair(left: Sequence[float], right: Sequence[float]) -> None:
    if not left or not right:
        raise ValueError("vectors must not be empty")
    if len(left) != len(right):
        raise ValueError("vectors must have the same length")
