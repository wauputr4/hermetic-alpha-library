"""Similarity helpers for chart-state vector encoding and search."""

from .encoding import encode_longitude, encode_planet_positions
from .search import (
    NearestNeighbor,
    SimilarityCandidate,
    cosine_similarity,
    euclidean_distance,
    find_nearest,
    nearest_neighbor_rows,
)

__all__ = [
    "NearestNeighbor",
    "SimilarityCandidate",
    "cosine_similarity",
    "encode_longitude",
    "encode_planet_positions",
    "euclidean_distance",
    "find_nearest",
    "nearest_neighbor_rows",
]
