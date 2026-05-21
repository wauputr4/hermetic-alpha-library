from datetime import datetime, timedelta, timezone
from math import isclose

import pytest

from hermetic_alpha.exports import to_csv
from hermetic_alpha.models import PlanetPosition
from hermetic_alpha.similarity import (
    SimilarityCandidate,
    cosine_similarity,
    encode_longitude,
    encode_planet_positions,
    euclidean_distance,
    find_nearest,
    nearest_neighbor_rows,
    nearest_neighbor_summary_row,
    planet_position_encoding_rows,
    planet_position_vector_summary_row,
)


def test_encode_longitude_normalizes_circular_degrees():
    sin_a, cos_a = encode_longitude(359)
    sin_b, cos_b = encode_longitude(-1)

    assert isclose(sin_a, sin_b, abs_tol=1e-12)
    assert isclose(cos_a, cos_b, abs_tol=1e-12)


def test_encode_longitude_keeps_nearby_wraparound_values_close():
    sin_359, cos_359 = encode_longitude(359)
    sin_1, cos_1 = encode_longitude(1)

    distance = ((sin_359 - sin_1) ** 2 + (cos_359 - cos_1) ** 2) ** 0.5
    assert distance < 0.04


def test_encode_planet_positions_uses_stable_timestamp_body_ordering():
    early = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
    positions = [
        PlanetPosition(later, "moon", 180),
        PlanetPosition(early, "sun", 90),
        PlanetPosition(early, "jupiter", 0),
    ]

    vector = encode_planet_positions(positions)

    assert vector == [
        *encode_longitude(0),
        *encode_longitude(90),
        *encode_longitude(180),
    ]


def test_encode_planet_positions_compares_aware_timestamps_chronologically():
    utc = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    same_instant_wib = datetime(
        2026, 5, 17, 7, 0, tzinfo=timezone(timedelta(hours=7))
    )
    positions = [
        PlanetPosition(same_instant_wib, "sun", 90),
        PlanetPosition(utc, "jupiter", 0),
    ]

    vector = encode_planet_positions(positions)

    assert vector == [
        *encode_longitude(0),
        *encode_longitude(90),
    ]


def test_planet_position_encoding_rows_match_vector_component_order():
    early = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
    positions = [
        PlanetPosition(later, "moon", 180),
        PlanetPosition(early, "sun", 90, zodiac="sidereal"),
        PlanetPosition(early, "sun", 45, zodiac="tropical"),
        PlanetPosition(early, "jupiter", 0),
    ]

    rows = planet_position_encoding_rows(positions)
    vector = encode_planet_positions(positions)

    assert [row["position_index"] for row in rows] == [0, 1, 2, 3]
    assert [(row["timestamp"], row["body"], row["zodiac"]) for row in rows] == [
        (early, "jupiter", "tropical"),
        (early, "sun", "sidereal"),
        (early, "sun", "tropical"),
        (later, "moon", "tropical"),
    ]
    assert [
        component
        for row in rows
        for component in (row["longitude_sin"], row["longitude_cos"])
    ] == vector


def test_planet_position_encoding_rows_keep_circular_components_inspectable():
    timestamp = datetime(2026, 5, 17, tzinfo=timezone.utc)
    rows = planet_position_encoding_rows([
        PlanetPosition(timestamp, "sun", 359),
        PlanetPosition(timestamp, "moon", -1),
    ])

    moon_row, sun_row = rows

    assert moon_row["longitude"] == -1
    assert sun_row["longitude"] == 359
    assert moon_row["longitude_sin"] == pytest.approx(sun_row["longitude_sin"])
    assert moon_row["longitude_cos"] == pytest.approx(sun_row["longitude_cos"])


def test_planet_position_vector_summary_row_uses_sorted_boundary_metadata():
    early = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
    positions = [
        PlanetPosition(later, "moon", 180),
        PlanetPosition(early, "sun", 90, zodiac="sidereal"),
        PlanetPosition(early, "sun", 45, zodiac="tropical"),
        PlanetPosition(early, "jupiter", 0),
    ]

    row = planet_position_vector_summary_row(positions, chart_id="btc-2026-05-17")

    assert row == {
        "chart_id": "btc-2026-05-17",
        "position_count": 4,
        "vector_length": 8,
        "first_timestamp": early,
        "first_body": "jupiter",
        "first_zodiac": "tropical",
        "last_timestamp": later,
        "last_body": "moon",
        "last_zodiac": "tropical",
    }


def test_planet_position_vector_summary_row_handles_empty_positions():
    row = planet_position_vector_summary_row([])

    assert row == {
        "chart_id": None,
        "position_count": 0,
        "vector_length": 0,
        "first_timestamp": None,
        "first_body": None,
        "first_zodiac": None,
        "last_timestamp": None,
        "last_body": None,
        "last_zodiac": None,
    }


def test_find_nearest_ranks_similar_vectors_first_with_cosine_metric():
    query = [1.0, 0.0]
    candidates = [
        SimilarityCandidate("far", [0.0, 1.0], payload={"row": 2}),
        SimilarityCandidate("near", [0.99, 0.1], payload={"row": 1}),
    ]

    results = find_nearest(query, candidates)

    assert [result.id for result in results] == ["near", "far"]
    assert results[0].payload == {"row": 1}
    assert results[0].score > results[1].score


def test_find_nearest_supports_euclidean_metric_and_limit():
    results = find_nearest(
        [1.0, 1.0],
        [
            SimilarityCandidate("distant", [4.0, 4.0]),
            SimilarityCandidate("nearest", [1.5, 1.5]),
            SimilarityCandidate("middle", [2.0, 2.0]),
        ],
        limit=2,
        metric="euclidean",
    )

    assert [result.id for result in results] == ["nearest", "middle"]
    assert results[0].distance < results[1].distance


def test_find_nearest_breaks_exact_ties_by_candidate_id():
    results = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("b", [1.0, 0.0]),
            SimilarityCandidate("a", [1.0, 0.0]),
        ],
    )

    assert [result.id for result in results] == ["a", "b"]


def test_find_nearest_accepts_encoded_planet_position_vectors():
    timestamp = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    query = encode_planet_positions(
        [
            PlanetPosition(timestamp, "jupiter", 0),
            PlanetPosition(timestamp, "sun", 90),
        ]
    )
    nearest = encode_planet_positions(
        [
            PlanetPosition(timestamp, "jupiter", 1),
            PlanetPosition(timestamp, "sun", 89),
        ]
    )
    distant = encode_planet_positions(
        [
            PlanetPosition(timestamp, "jupiter", 180),
            PlanetPosition(timestamp, "sun", 270),
        ]
    )

    results = find_nearest(
        query,
        [
            SimilarityCandidate("distant-chart", distant),
            SimilarityCandidate("near-chart", nearest),
        ],
    )

    assert [result.id for result in results] == ["near-chart", "distant-chart"]


def test_nearest_neighbor_rows_preserves_ranked_order_and_scalar_payloads():
    results = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("far", [0.0, 1.0], payload="old-chart"),
            SimilarityCandidate("near", [1.0, 0.0], payload="current-chart"),
        ],
    )

    rows = nearest_neighbor_rows(results)

    assert [row["id"] for row in rows] == ["near", "far"]
    assert rows[0] == {
        "rank": 1,
        "id": "near",
        "score": 1.0,
        "distance": 0.0,
        "payload": "current-chart",
    }
    assert rows[1]["rank"] == 2
    assert rows[1]["payload"] == "old-chart"


def test_nearest_neighbor_rows_supports_explicit_mapping_payload_fields():
    results = find_nearest(
        [1.0, 1.0],
        [
            SimilarityCandidate(
                "nearest",
                [1.1, 1.1],
                payload={"timestamp": "2026-05-19", "asset": "BTC-USD", "nested": {"ignored": True}},
            ),
        ],
        metric="euclidean",
    )

    rows = nearest_neighbor_rows(results, payload_fields=["asset", "timestamp", "missing"])

    assert rows == [
        {
            "rank": 1,
            "id": "nearest",
            "score": -0.14142135623730964,
            "distance": 0.14142135623730964,
            "payload_asset": "BTC-USD",
            "payload_timestamp": "2026-05-19",
            "payload_missing": None,
        }
    ]


def test_nearest_neighbor_rows_rejects_selected_nested_payload_fields():
    results = find_nearest(
        [1.0],
        [
            SimilarityCandidate("nested", [1.0], payload={"metadata": {"asset": "BTC-USD"}}),
        ],
    )

    with pytest.raises(TypeError, match="payload field 'metadata' contains unsupported nested value dict"):
        nearest_neighbor_rows(results, payload_fields=["metadata"])


def test_nearest_neighbor_rows_requires_mapping_payload_for_payload_fields():
    results = find_nearest(
        [1.0],
        [
            SimilarityCandidate("list-payload", [1.0], payload=["BTC-USD"]),
        ],
    )

    with pytest.raises(TypeError, match="payload_fields requires mapping payload values"):
        nearest_neighbor_rows(results, payload_fields=["asset"])


def test_nearest_neighbor_summary_row_reports_ranked_result_boundaries():
    results = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("far", [0.0, 1.0], payload={"ignored": True}),
            SimilarityCandidate("near", [1.0, 0.0], payload={"ignored": False}),
        ],
        metric="cosine",
        limit=2,
    )

    row = nearest_neighbor_summary_row(results, query_id="query-a", metric="cosine", limit=2)

    assert row == {
        "query_id": "query-a",
        "metric": "cosine",
        "limit": 2,
        "result_count": 2,
        "top_id": "near",
        "top_score": 1.0,
        "top_distance": 0.0,
        "min_score": 0.0,
        "max_score": 1.0,
        "min_distance": 0.0,
        "max_distance": 1.0,
    }


def test_nearest_neighbor_summary_row_handles_empty_results():
    row = nearest_neighbor_summary_row([], query_id="query-empty", metric="euclidean", limit=5)

    assert row == {
        "query_id": "query-empty",
        "metric": "euclidean",
        "limit": 5,
        "result_count": 0,
        "top_id": None,
        "top_score": None,
        "top_distance": None,
        "min_score": None,
        "max_score": None,
        "min_distance": None,
        "max_distance": None,
    }


def test_nearest_neighbor_summary_row_is_csv_compatible():
    results = find_nearest(
        [1.0, 1.0],
        [SimilarityCandidate("nearest", [1.1, 1.1])],
        metric="euclidean",
    )

    text = to_csv([nearest_neighbor_summary_row(results, query_id="query-b", metric="euclidean")])

    assert text.splitlines()[0] == (
        "query_id,metric,limit,result_count,top_id,top_score,top_distance,"
        "min_score,max_score,min_distance,max_distance"
    )
    assert "query-b,euclidean,,1,nearest,-0.14142135623730964,0.14142135623730964" in text


def test_similarity_search_validates_inputs():
    assert find_nearest([1.0], []) == []

    with pytest.raises(ValueError, match="vectors must have the same length"):
        cosine_similarity([1.0], [1.0, 2.0])

    with pytest.raises(ValueError, match="cosine similarity requires non-zero vectors"):
        cosine_similarity([0.0, 0.0], [1.0, 0.0])

    with pytest.raises(ValueError, match="vectors must not be empty"):
        euclidean_distance([], [])

    with pytest.raises(ValueError, match="limit must be a positive integer"):
        find_nearest([1.0], [SimilarityCandidate("a", [1.0])], limit=0)

    with pytest.raises(ValueError, match="metric must be 'cosine' or 'euclidean'"):
        find_nearest([1.0], [SimilarityCandidate("a", [1.0])], metric="manhattan")
