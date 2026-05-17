"""Dependency-free nearest-neighbor search for numeric chart vectors."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt
from typing import Any, Literal

SimilarityMetric = Literal["cosine", "euclidean"]


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


def _validate_pair(left: Sequence[float], right: Sequence[float]) -> None:
    if not left or not right:
        raise ValueError("vectors must not be empty")
    if len(left) != len(right):
        raise ValueError("vectors must have the same length")
