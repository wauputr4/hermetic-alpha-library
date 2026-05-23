"""Similarity helpers for chart-state vector encoding and search."""

from .encoding import (
    encode_longitude,
    encode_planet_positions,
    planet_position_encoding_rows,
    planet_position_vector_summary_row,
    planet_position_vector_summary_rows,
)
from .search import (
    NearestNeighbor,
    SimilarityCandidate,
    cosine_similarity,
    euclidean_distance,
    find_nearest,
    nearest_neighbor_group_rows,
    nearest_neighbor_rows,
    nearest_neighbor_summary_row,
    nearest_neighbor_summary_rows,
)

__all__ = [
    "NearestNeighbor",
    "SimilarityCandidate",
    "cosine_similarity",
    "encode_longitude",
    "encode_planet_positions",
    "euclidean_distance",
    "find_nearest",
    "nearest_neighbor_group_rows",
    "nearest_neighbor_rows",
    "nearest_neighbor_summary_row",
    "nearest_neighbor_summary_rows",
    "planet_position_encoding_rows",
    "planet_position_vector_summary_row",
    "planet_position_vector_summary_rows",
]
