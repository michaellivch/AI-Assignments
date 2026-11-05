"""Tests for UCS/Dijkstra routing on synthetic and provided city graphs."""

import math
from pathlib import Path

import pytest

from src.models import Road
from src.parser import load_scenario
from src.search import find_shortest_path

SCENARIOS = Path(__file__).resolve().parent.parent / "Scenarios"


def road(source: str, destination: str, travel_time: float) -> Road:
    """Create a directed road with the given normal travel time."""
    return Road(source, destination, travel_time * 10, "urban", 10)


@pytest.fixture
def example_roads() -> list[Road]:
    """Graph where the fewest edges do not give the fastest route."""
    return [
        road("S", "G", 20),
        road("S", "A", 3),
        road("A", "G", 15),
        road("S", "B", 2),
        road("B", "C", 2),
        road("C", "G", 4),
    ]


def test_shortest_weighted_path(example_roads):
    """Prefer the minimum travel-time route rather than fewest roads."""
    path, cost = find_shortest_path(example_roads, "S", "G")
    assert path == ["S", "B", "C", "G"]
    assert cost == pytest.approx(8)


def test_directed_roads():
    """An A-to-B road does not automatically allow B-to-A travel."""
    path, cost = find_shortest_path([road("A", "B", 5)], "B", "A")
    assert path == []
    assert math.isinf(cost)


def test_start_equals_goal():
    """No travel is necessary when already at the incident node."""
    path, cost = find_shortest_path([road("A", "B", 5)], "A", "A")
    assert path == ["A"]
    assert cost == 0


def test_unreachable_destination():
    """Disconnected portions of the graph have no valid route."""
    path, cost = find_shortest_path(
        [road("A", "B", 3), road("C", "D", 2)], "A", "D"
    )
    assert path == []
    assert cost == math.inf


def test_blocked_road_reroutes(example_roads):
    """An infinite road cost excludes a blocked directed road."""
    path, cost = find_shortest_path(
        example_roads, "S", "G", {("B", "C"): math.inf}
    )
    assert path == ["S", "A", "G"]
    assert cost == pytest.approx(18)


def test_congestion_changes_best_route(example_roads):
    """Updated road travel times may change the optimal route."""
    path, cost = find_shortest_path(
        example_roads, "S", "G", {("B", "C"): 20}
    )
    assert path == ["S", "A", "G"]
    assert cost == pytest.approx(18)


def test_cost_override_is_directional():
    """A cost override for A-to-B does not affect B-to-A."""
    roads = [road("A", "B", 4), road("B", "A", 7)]
    path, cost = find_shortest_path(roads, "B", "A", {("A", "B"): math.inf})
    assert path == ["B", "A"]
    assert cost == pytest.approx(7)


def test_can_reroute_after_new_costs(example_roads):
    """Repeated searches use the latest supplied snapshot of road costs."""
    normal_path, _ = find_shortest_path(example_roads, "S", "G")
    altered_path, _ = find_shortest_path(
        example_roads, "S", "G", {("B", "C"): math.inf}
    )
    assert normal_path != altered_path


@pytest.mark.parametrize("invalid_cost", [-1, -math.inf, math.nan])
def test_reject_invalid_costs(example_roads, invalid_cost):
    """Dijkstra requires nonnegative, non-NaN weights."""
    with pytest.raises(ValueError):
        find_shortest_path(example_roads, "S", "G", {("S", "G"): invalid_cost})


@pytest.mark.parametrize("speed", [0, -2])
def test_reject_invalid_road_speed(speed):
    """Invalid base travel speed is rejected even with an override."""
    roads = [Road("A", "B", 10, "urban", speed)]
    with pytest.raises(ValueError):
        find_shortest_path(roads, "A", "B", {("A", "B"): 5})


@pytest.mark.parametrize("distance", [-1, math.inf, math.nan])
def test_reject_invalid_road_distance(distance):
    """Invalid distances must not be silently accepted."""
    with pytest.raises(ValueError):
        find_shortest_path([Road("A", "B", distance, "urban", 10)], "A", "B")


def test_reject_duplicate_directed_roads():
    """Duplicate edge identifiers make the override mapping ambiguous."""
    with pytest.raises(ValueError, match="Duplicate"):
        find_shortest_path([road("A", "B", 2), road("A", "B", 5)], "A", "B")


@pytest.mark.parametrize("start,goal", [("missing", "B"), ("A", "missing")])
def test_reject_unknown_nodes(start, goal):
    """Mistyped node identifiers should cause an explicit error."""
    with pytest.raises(KeyError):
        find_shortest_path([road("A", "B", 2)], start, goal)


def test_reject_unknown_override_road():
    """An override for a nonexistent directed edge should fail."""
    with pytest.raises(KeyError):
        find_shortest_path([road("A", "B", 2)], "A", "B", {("B", "A"): 3})


def test_blocking_all_routes():
    """Returns no route if every outgoing road is blocked."""
    path, cost = find_shortest_path(
        [road("A", "B", 2)], "A", "B", {("A", "B"): math.inf}
    )
    assert path == []
    assert math.isinf(cost)


def test_fractional_travel_time():
    """Travel times may be fractional seconds."""
    path, cost = find_shortest_path([Road("A", "B", 25, "urban", 10)], "A", "B")
    assert path == ["A", "B"]
    assert cost == pytest.approx(2.5)


@pytest.mark.parametrize("scenario_name", ["Scenario1", "Scenario2", "Scenario3"])
def test_real_scenario_routes(scenario_name):
    """Real scenario graph supports finding and validating a route."""
    scenario = load_scenario(SCENARIOS / scenario_name)
    start = scenario.responders[0].start_location
    goal = scenario.incidents[0].location

    path, cost = find_shortest_path(scenario.roads, start, goal)
    assert path[0] == start
    assert path[-1] == goal
    assert cost >= 0 and math.isfinite(cost)

    edge_lookup = {(r.from_node, r.to_node): r for r in scenario.roads}
    assert all((a, b) in edge_lookup for a, b in zip(path, path[1:]))
    computed_cost = sum(
        edge_lookup[(a, b)].normal_travel_time()
        for a, b in zip(path, path[1:])
    )
    assert cost == pytest.approx(computed_cost)
