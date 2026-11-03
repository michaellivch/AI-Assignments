"""Tests for the scenario parser.

Tests loading the provided scenarios, data type conversions,
missing files, invalid data, and edge cases.

Temporary scenario copies are used so the original data
is never modified.
"""

import csv
import json
import shutil
from pathlib import Path

import pytest

from src.models import Node, Responder, Incident, Road
from src.parser import load_scenario, read_json, read_csv

# Path to the original scenario directories.
SCENARIOS = Path(__file__).resolve().parent.parent / "Scenarios"

@pytest.fixture
def scenario_copy(tmp_path):
    """Create a temporary copy of Scenario1 for testing.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        Path to the copied scenario directory.
    """
    destination = tmp_path / "Scenario1"

    shutil.copytree(
        SCENARIOS / "Scenario1",
        destination
    )

    return destination

def update_csv(file_path, modify_rows):
    """Modify a CSV file while keeping its original columns.

    Args:
        file_path: Path to the CSV file.
        modify_rows: Function that modifies the list of rows.
    """
    rows = read_csv(file_path)

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        fieldnames = csv.DictReader(file).fieldnames

    modify_rows(rows)

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# ============================================================
# 1. TEST LOADING VALID SCENARIOS
# ============================================================

@pytest.mark.parametrize(
    "scenario_name",
    ["Scenario1", "Scenario2", "Scenario3"]
)
def test_scenario_loads(scenario_name):
    """Every provided scenario should load successfully."""
    scenario = load_scenario(SCENARIOS / scenario_name)

    assert len(scenario.nodes) > 0
    assert len(scenario.roads) > 0
    assert len(scenario.responders) > 0
    assert len(scenario.incidents) > 0

@pytest.mark.parametrize(
    "scenario_name, expected_nodes, expected_roads, expected_responders, expected_incidents",
    [
        ("Scenario1", 5, 14, 4, 7),
        ("Scenario2", 12, 30, 10, 12),
        ("Scenario3", 26, 60, 10, 20),
    ]
)
def test_scenario_counts(
    scenario_name,
    expected_nodes,
    expected_roads,
    expected_responders,
    expected_incidents
):
    """Verify the exact number of objects in each scenario."""
    scenario = load_scenario(SCENARIOS / scenario_name)

    assert len(scenario.nodes) == expected_nodes
    assert len(scenario.roads) == expected_roads
    assert len(scenario.responders) == expected_responders
    assert len(scenario.incidents) == expected_incidents

@pytest.mark.parametrize(
    "scenario_name",
    ["Scenario1", "Scenario2", "Scenario3"]
)
def test_parsed_types(scenario_name):
    """Verify correct Python object types for all scenarios."""
    scenario = load_scenario(SCENARIOS / scenario_name)

    assert all(isinstance(node, Node) for node in scenario.nodes.values())
    assert all(isinstance(road, Road) for road in scenario.roads)
    assert all(isinstance(r, Responder) for r in scenario.responders)
    assert all(isinstance(i, Incident) for i in scenario.incidents)
    assert all(isinstance(r.capabilities, set) for r in scenario.responders)
    """Check that parsed records use the correct model classes."""
    scenario = load_scenario(SCENARIOS / "Scenario1")

    assert all(
        isinstance(node, Node)
        for node in scenario.nodes.values()
    )

    assert all(
        isinstance(responder, Responder)
        for responder in scenario.responders
    )

    assert all(
        isinstance(incident, Incident)
        for incident in scenario.incidents
    )

    assert isinstance(scenario.responders[0].capabilities, set)

# ============================================================
# 2. TEST DATA CONVERSIONS
# ============================================================

def test_multiple_capabilities(scenario_copy):
    """Semicolon-separated capabilities become a set."""
    file_path = scenario_copy / "responders.csv"

    def modify(rows):
        rows[0]["capabilities"] = "medical;fire;rescue"

    update_csv(file_path, modify)

    scenario = load_scenario(scenario_copy)

    assert scenario.responders[0].capabilities == {
        "medical", "fire", "rescue"
    }

def test_empty_capabilities(scenario_copy):
    """An empty capabilities field should produce an empty set."""
    file_path = scenario_copy / "responders.csv"

    def modify(rows):
        rows[0]["capabilities"] = ""

    update_csv(file_path, modify)

    scenario = load_scenario(scenario_copy)

    assert scenario.responders[0].capabilities == set()

def test_numeric_conversions():
    """Numeric scenario fields should become int or float values."""
    scenario = load_scenario(SCENARIOS / "Scenario1")

    assert isinstance(scenario.roads[0].distance, float)
    assert isinstance(scenario.roads[0].speed, float)

    assert isinstance(scenario.incidents[0].deadline, float)
    assert isinstance(scenario.incidents[0].timestamp, float)
    assert isinstance(scenario.incidents[0].time_required, float)

    assert isinstance(
        scenario.responders[0].time_until_available,
        float
    )

    assert isinstance(
        scenario.traffic_observations[0].observation_nr,
        int
    )

def test_empty_incident_list(scenario_copy):
    """A CSV containing only headers should give zero incidents."""
    file_path = scenario_copy / "incidents.csv"

    update_csv(file_path, lambda rows: rows.clear())

    scenario = load_scenario(scenario_copy)

    assert scenario.incidents == []

# ============================================================
# 3. TEST MISSING FILES AND DIRECTORIES
# ============================================================

def test_missing_scenario():
    """A nonexistent scenario directory must raise an error."""
    with pytest.raises(FileNotFoundError):
        load_scenario(SCENARIOS / "DoesNotExist")

def test_missing_input_file(scenario_copy):
    """A missing required input file must raise an error."""
    (scenario_copy / "responders.csv").unlink()

    with pytest.raises(FileNotFoundError):
        load_scenario(scenario_copy)

# ============================================================
# 4. TEST INVALID INPUT DATA
# ============================================================

def test_invalid_json(tmp_path):
    """Malformed JSON must raise a JSON decoding error."""
    file_path = tmp_path / "invalid.json"

    file_path.write_text(
        "{invalid JSON",
        encoding="utf-8"
    )

    with pytest.raises(json.JSONDecodeError):
        read_json(file_path)

def test_missing_csv_column(scenario_copy):
    """A missing required CSV field must raise KeyError."""
    file_path = scenario_copy / "responders.csv"

    rows = read_csv(file_path)

    # Remove the capabilities column entirely.
    for row in rows:
        row.pop("capabilities")

    fieldnames = [
        name for name in rows[0].keys()
    ]

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(KeyError):
        load_scenario(scenario_copy)

def test_invalid_numeric_value(scenario_copy):
    """An invalid numeric value should raise ValueError."""
    file_path = scenario_copy / "responders.csv"

    def modify(rows):
        rows[0]["time_until_available"] = "soon"

    update_csv(file_path, modify)

    with pytest.raises(ValueError):
        load_scenario(scenario_copy)

def test_invalid_road_distance(scenario_copy):
    """A nonnumeric road distance must raise ValueError."""
    file_path = scenario_copy / "city_graph.json"

    graph = read_json(file_path)
    graph["roads"][0]["distance"] = "unknown"

    file_path.write_text(
        json.dumps(graph),
        encoding="utf-8"
    )

    with pytest.raises(ValueError):
        load_scenario(scenario_copy)

# ============================================================
# 5. TEST EDGE CASES
# ============================================================

def test_zero_road_speed(scenario_copy):
    """A zero speed should be rejected when calculating travel time."""
    file_path = scenario_copy / "city_graph.json"

    graph = read_json(file_path)
    graph["roads"][0]["speed"] = 0

    file_path.write_text(
        json.dumps(graph),
        encoding="utf-8"
    )

    scenario = load_scenario(scenario_copy)

    with pytest.raises(ValueError):
        scenario.roads[0].normal_travel_time()

def test_read_csv_empty_file(tmp_path):
    """An empty CSV should return an empty list."""
    file_path = tmp_path / "empty.csv"
    file_path.write_text("", encoding="utf-8")

    assert read_csv(file_path) == []