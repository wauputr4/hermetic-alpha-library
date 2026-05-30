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
    nearest_neighbor_group_rows,
    nearest_neighbor_rows,
    nearest_neighbor_summary_row,
    nearest_neighbor_summary_rows,
    planet_position_encoding_group_rows,
    planet_position_encoding_rows,
    planet_position_vector_summary_row,
    planet_position_vector_summary_rows,
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


def test_encode_planet_positions_rejects_malformed_position_values():
    with pytest.raises(ValueError, match="PlanetPosition values"):
        encode_planet_positions([object()])


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


def test_planet_position_encoding_rows_rejects_malformed_position_values():
    with pytest.raises(ValueError, match="PlanetPosition values"):
        planet_position_encoding_rows([object()])


def test_planet_position_encoding_group_rows_preserves_ordered_mapping_order():
    early = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)

    rows = planet_position_encoding_group_rows(
        {
            "chart-a": [PlanetPosition(early, "sun", 90)],
            "chart-b": [PlanetPosition(later, "moon", 180)],
        }
    )

    assert [row["chart_id"] for row in rows] == ["chart-a", "chart-b"]
    assert [row["timestamp"] for row in rows] == [early, later]
    assert [row["position_index"] for row in rows] == [0, 0]


def test_planet_position_encoding_group_rows_accepts_pairs_and_skips_empty_groups():
    ts = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)

    rows = planet_position_encoding_group_rows(
        [
            ("empty", []),
            (
                "chart-a",
                [
                    PlanetPosition(ts, "sun", 90),
                    PlanetPosition(ts, "moon", 180),
                ],
            ),
        ]
    )

    assert [row["chart_id"] for row in rows] == ["chart-a", "chart-a"]
    assert [row["body"] for row in rows] == ["moon", "sun"]


def test_planet_position_encoding_group_rows_rejects_duplicate_chart_ids():
    ts = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    positions = [PlanetPosition(ts, "sun", 90)]

    with pytest.raises(ValueError, match="chart IDs must be unique"):
        planet_position_encoding_group_rows([("chart-a", positions), ("chart-a", positions)])


def test_planet_position_encoding_group_rows_rejects_blank_chart_ids():
    with pytest.raises(ValueError, match="chart ID must not be blank"):
        planet_position_encoding_group_rows([("   ", [])])


def test_planet_position_encoding_group_rows_rejects_whitespace_padded_chart_ids():
    with pytest.raises(ValueError, match="chart ID must not include leading or trailing whitespace"):
        planet_position_encoding_group_rows([("train ", [])])

    with pytest.raises(ValueError, match="chart ID must not include leading or trailing whitespace"):
        planet_position_encoding_group_rows([(" train", [])])


def test_planet_position_encoding_group_rows_rejects_non_string_chart_ids():
    with pytest.raises(ValueError, match="chart ID must be a string"):
        planet_position_encoding_group_rows([(123, [])])


@pytest.mark.parametrize(
    "charts",
    [
        ["chart-a"],
        [("chart-a",)],
        [("chart-a", [], "extra")],
    ],
)
def test_planet_position_encoding_group_rows_rejects_malformed_ordered_entries(charts):
    with pytest.raises(ValueError, match="two-item \\(chart_id, positions\\) pair"):
        planet_position_encoding_group_rows(charts)


def test_planet_position_encoding_group_rows_rejects_malformed_position_values():
    with pytest.raises(ValueError, match="PlanetPosition values"):
        planet_position_encoding_group_rows([("query", [object()])])


def test_planet_position_encoding_group_rows_are_csv_compatible():
    ts = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)

    text = to_csv(
        planet_position_encoding_group_rows(
            [("chart-a", [PlanetPosition(ts, "sun", 90)]), ("empty", [])]
        )
    )

    assert text.splitlines()[0] == (
        "chart_id,position_index,timestamp,body,zodiac,longitude,longitude_sin,longitude_cos"
    )
    assert "\nchart-a,0,2026-05-17T00:00:00+00:00,sun,tropical,90," in text


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


def test_planet_position_vector_summary_row_rejects_malformed_position_values():
    with pytest.raises(ValueError, match="PlanetPosition values"):
        planet_position_vector_summary_row([object()])


def test_planet_position_vector_summary_rows_preserves_ordered_mapping_order():
    early = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    later = datetime(2026, 5, 18, 0, 0, tzinfo=timezone.utc)
    first = [PlanetPosition(early, "sun", 90)]
    second = [PlanetPosition(later, "moon", 180)]

    rows = planet_position_vector_summary_rows({"chart-a": first, "chart-b": second})

    assert [row["chart_id"] for row in rows] == ["chart-a", "chart-b"]
    assert rows[0]["first_timestamp"] == early
    assert rows[1]["first_timestamp"] == later


def test_planet_position_vector_summary_rows_accepts_ordered_pairs_and_empty_positions():
    ts = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    positions = [PlanetPosition(ts, "sun", 90)]

    rows = planet_position_vector_summary_rows([("empty", []), ("active", positions)])

    assert [row["chart_id"] for row in rows] == ["empty", "active"]
    assert rows[0]["position_count"] == 0
    assert rows[0]["first_timestamp"] is None
    assert rows[1]["position_count"] == 1


def test_planet_position_vector_summary_rows_rejects_duplicate_chart_ids():
    ts = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    positions = [PlanetPosition(ts, "sun", 90)]

    with pytest.raises(ValueError, match="chart IDs must be unique"):
        planet_position_vector_summary_rows([("chart-a", positions), ("chart-a", positions)])


def test_planet_position_vector_summary_rows_rejects_blank_chart_ids():
    with pytest.raises(ValueError, match="chart ID must not be blank"):
        planet_position_vector_summary_rows([("   ", [])])


def test_planet_position_vector_summary_rows_rejects_whitespace_padded_chart_ids():
    with pytest.raises(ValueError, match="chart ID must not include leading or trailing whitespace"):
        planet_position_vector_summary_rows([(" train", [])])

    with pytest.raises(ValueError, match="chart ID must not include leading or trailing whitespace"):
        planet_position_vector_summary_rows([("train ", [])])


def test_planet_position_vector_summary_rows_rejects_non_string_chart_ids():
    with pytest.raises(ValueError, match="chart ID must be a string"):
        planet_position_vector_summary_rows([(123, [])])


@pytest.mark.parametrize(
    "charts",
    [
        ["chart-a"],
        [("chart-a",)],
        [("chart-a", [], "extra")],
    ],
)
def test_planet_position_vector_summary_rows_rejects_malformed_ordered_entries(charts):
    with pytest.raises(ValueError, match="two-item \\(chart_id, positions\\) pair"):
        planet_position_vector_summary_rows(charts)


def test_planet_position_vector_summary_rows_rejects_malformed_position_values():
    with pytest.raises(ValueError, match="PlanetPosition values"):
        planet_position_vector_summary_rows([("query", [object()])])


def test_planet_position_vector_summary_rows_are_csv_compatible():
    ts = datetime(2026, 5, 17, 0, 0, tzinfo=timezone.utc)
    rows = planet_position_vector_summary_rows(
        [("chart-a", [PlanetPosition(ts, "sun", 90)]), ("empty", [])]
    )

    text = to_csv(rows)

    assert text.splitlines()[0] == (
        "chart_id,position_count,vector_length,first_timestamp,first_body,"
        "first_zodiac,last_timestamp,last_body,last_zodiac"
    )
    assert "chart-a,1,2,2026-05-17T00:00:00+00:00,sun,tropical" in text
    assert "empty,0,0,,,,,," in text


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


def test_nearest_neighbor_rows_rejects_blank_payload_field_names_before_rows():
    results = find_nearest(
        [1.0],
        [
            SimilarityCandidate("scalar", [1.0], payload="BTC-USD"),
        ],
    )

    with pytest.raises(ValueError, match="payload field names must be non-blank strings"):
        nearest_neighbor_rows(results, payload_fields=["asset", " "])


def test_nearest_neighbor_rows_requires_mapping_payload_for_payload_fields():
    results = find_nearest(
        [1.0],
        [
            SimilarityCandidate("list-payload", [1.0], payload=["BTC-USD"]),
        ],
    )

    with pytest.raises(TypeError, match="payload_fields requires mapping payload values"):
        nearest_neighbor_rows(results, payload_fields=["asset"])


def test_nearest_neighbor_group_rows_preserves_ordered_mapping_input():
    search_a = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("far", [0.0, 1.0]),
            SimilarityCandidate("near", [1.0, 0.0]),
        ],
    )
    search_b = find_nearest([0.0, 1.0], [SimilarityCandidate("match", [0.0, 1.0])])

    rows = nearest_neighbor_group_rows({"search-a": search_a, "search-b": search_b})

    assert [row["search_id"] for row in rows] == ["search-a", "search-a", "search-b"]
    assert [row["rank"] for row in rows] == [1, 2, 1]
    assert [row["id"] for row in rows] == ["near", "far", "match"]


def test_nearest_neighbor_group_rows_accepts_pair_input_skips_empty_groups_and_forwards_payload_fields():
    rows = nearest_neighbor_group_rows(
        [
            ("empty-search", []),
            (
                "payload-search",
                find_nearest(
                    [1.0, 0.0],
                    [SimilarityCandidate("near", [1.0, 0.0], payload={"asset": "BTC-USD"})],
                ),
            ),
        ],
        payload_fields=["asset", "missing"],
    )

    assert rows == [
        {
            "search_id": "payload-search",
            "rank": 1,
            "id": "near",
            "score": 1.0,
            "distance": 0.0,
            "payload_asset": "BTC-USD",
            "payload_missing": None,
        }
    ]


def test_nearest_neighbor_group_rows_rejects_duplicate_and_blank_search_ids():
    with pytest.raises(ValueError, match="search IDs must be unique"):
        nearest_neighbor_group_rows([("same", []), ("same", [])])

    with pytest.raises(ValueError, match="search ID must not be blank"):
        nearest_neighbor_group_rows([(" ", [])])


def test_nearest_neighbor_group_rows_rejects_whitespace_padded_search_ids():
    with pytest.raises(ValueError, match="search ID must not include leading or trailing whitespace"):
        nearest_neighbor_group_rows([(" train", [])])

    with pytest.raises(ValueError, match="search ID must not include leading or trailing whitespace"):
        nearest_neighbor_group_rows([("train ", [])])


def test_nearest_neighbor_group_rows_rejects_non_string_search_ids():
    with pytest.raises(ValueError, match="search ID must be a string"):
        nearest_neighbor_group_rows({123: []})

    with pytest.raises(ValueError, match="search ID must be a string"):
        nearest_neighbor_group_rows([(123, [])])


@pytest.mark.parametrize(
    "searches",
    [
        ["search-a"],
        [("search-a",)],
        [("search-a", [], "extra")],
    ],
)
def test_nearest_neighbor_group_rows_rejects_malformed_ordered_entries(searches):
    with pytest.raises(ValueError, match="two-item \\(search_id, results\\) pair"):
        nearest_neighbor_group_rows(searches)


def test_nearest_neighbor_group_rows_rejects_blank_payload_field_names():
    with pytest.raises(ValueError, match="payload field names must be non-blank strings"):
        nearest_neighbor_group_rows([("empty-search", [])], payload_fields=["asset", ""])


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


def test_nearest_neighbor_summary_rows_preserves_ordered_mapping_input():
    query_a = find_nearest(
        [1.0, 0.0],
        [
            SimilarityCandidate("far", [0.0, 1.0]),
            SimilarityCandidate("near", [1.0, 0.0]),
        ],
    )
    query_b = find_nearest([0.0, 1.0], [SimilarityCandidate("match", [0.0, 1.0])])

    rows = nearest_neighbor_summary_rows(
        {"search-a": query_a, "search-b": query_b},
        query_ids={"search-a": "btc-query", "search-b": "eth-query"},
        metrics={"search-a": "cosine", "search-b": "cosine"},
        limits={"search-a": 2, "search-b": 1},
    )

    assert [row["search_id"] for row in rows] == ["search-a", "search-b"]
    assert rows[0] == {
        "search_id": "search-a",
        "query_id": "btc-query",
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
    assert rows[1]["top_id"] == "match"


def test_nearest_neighbor_summary_rows_accepts_pair_input_and_empty_results():
    rows = nearest_neighbor_summary_rows(
        [
            ("empty-search", []),
            ("euclidean-search", find_nearest([1.0], [SimilarityCandidate("close", [1.5])], metric="euclidean")),
        ],
        query_ids=[("empty-search", "empty-query"), ("euclidean-search", "distance-query")],
        metrics=[("empty-search", "cosine"), ("euclidean-search", "euclidean")],
        limits=[("empty-search", 5), ("euclidean-search", None)],
    )

    assert rows[0] == {
        "search_id": "empty-search",
        "query_id": "empty-query",
        "metric": "cosine",
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
    assert rows[1]["search_id"] == "euclidean-search"
    assert rows[1]["top_id"] == "close"


def test_nearest_neighbor_summary_rows_rejects_duplicate_and_blank_search_ids():
    with pytest.raises(ValueError, match="search IDs must be unique"):
        nearest_neighbor_summary_rows([("same", []), ("same", [])])

    with pytest.raises(ValueError, match="search ID must not be blank"):
        nearest_neighbor_summary_rows([(" ", [])])


def test_nearest_neighbor_summary_rows_rejects_whitespace_padded_search_ids():
    with pytest.raises(ValueError, match="search ID must not include leading or trailing whitespace"):
        nearest_neighbor_summary_rows([(" train", [])])

    with pytest.raises(ValueError, match="search ID must not include leading or trailing whitespace"):
        nearest_neighbor_summary_rows([("train ", [])])


def test_nearest_neighbor_summary_rows_rejects_non_string_search_ids():
    with pytest.raises(ValueError, match="search ID must be a string"):
        nearest_neighbor_summary_rows({123: []})

    with pytest.raises(ValueError, match="search ID must be a string"):
        nearest_neighbor_summary_rows([(123, [])])


@pytest.mark.parametrize(
    "searches",
    [
        ["search-a"],
        [("search-a",)],
        [("search-a", [], "extra")],
    ],
)
def test_nearest_neighbor_summary_rows_rejects_malformed_ordered_entries(searches):
    with pytest.raises(ValueError, match="two-item \\(search_id, results\\) pair"):
        nearest_neighbor_summary_rows(searches)


def test_nearest_neighbor_summary_rows_rejects_duplicate_metadata_ids():
    with pytest.raises(ValueError, match="query ID search IDs must be unique"):
        nearest_neighbor_summary_rows(
            {"search": []},
            query_ids=[("search", "first"), ("search", "second")],
        )

    with pytest.raises(ValueError, match="metric search ID must not be blank"):
        nearest_neighbor_summary_rows({"search": []}, metrics=[(" ", "cosine")])


def test_nearest_neighbor_summary_rows_rejects_whitespace_padded_metadata_ids():
    with pytest.raises(ValueError, match="query ID search ID must not include leading or trailing whitespace"):
        nearest_neighbor_summary_rows({"search": []}, query_ids=[(" search", "query")])

    with pytest.raises(ValueError, match="metric search ID must not include leading or trailing whitespace"):
        nearest_neighbor_summary_rows({"search": []}, metrics=[("search ", "cosine")])

    with pytest.raises(ValueError, match="limit search ID must not include leading or trailing whitespace"):
        nearest_neighbor_summary_rows({"search": []}, limits={" search": 3})


def test_nearest_neighbor_summary_rows_rejects_non_string_metadata_ids():
    with pytest.raises(ValueError, match="query ID search ID must be a string"):
        nearest_neighbor_summary_rows({"search": []}, query_ids={123: "query"})

    with pytest.raises(ValueError, match="metric search ID must be a string"):
        nearest_neighbor_summary_rows({"search": []}, metrics=[(123, "cosine")])

    with pytest.raises(ValueError, match="limit search ID must be a string"):
        nearest_neighbor_summary_rows({"search": []}, limits={123: 3})


def test_nearest_neighbor_summary_rows_rejects_unknown_metadata_ids():
    searches = {"declared": []}

    with pytest.raises(ValueError, match="query ID search IDs must match declared searches"):
        nearest_neighbor_summary_rows(searches, query_ids={"unknown": "query"})

    with pytest.raises(ValueError, match="metric search IDs must match declared searches"):
        nearest_neighbor_summary_rows(searches, metrics={"unknown": "cosine"})

    with pytest.raises(ValueError, match="limit search IDs must match declared searches"):
        nearest_neighbor_summary_rows(searches, limits={"unknown": 3})


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"query_ids": ["search"]}, "query ID metadata entry 0"),
        ({"metrics": [("search",)]}, "metric metadata entry 0"),
        ({"limits": [("search", 3, "extra")]}, "limit metadata entry 0"),
    ],
)
def test_nearest_neighbor_summary_rows_rejects_malformed_metadata_entries(kwargs, message):
    with pytest.raises(ValueError, match=message):
        nearest_neighbor_summary_rows({"search": []}, **kwargs)


def test_nearest_neighbor_summary_rows_is_csv_compatible():
    results = find_nearest(
        [1.0, 0.0],
        [SimilarityCandidate("near", [1.0, 0.0])],
        metric="cosine",
    )

    text = to_csv(nearest_neighbor_summary_rows({"search-a": results}, metrics={"search-a": "cosine"}))

    assert text.splitlines()[0] == (
        "search_id,query_id,metric,limit,result_count,top_id,top_score,top_distance,"
        "min_score,max_score,min_distance,max_distance"
    )
    assert "\nsearch-a,,cosine,,1,near,1.0,0.0,1.0,1.0,0.0,0.0" in text


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
