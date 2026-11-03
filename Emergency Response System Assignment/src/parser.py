"""Load an Emergency Response System scenario into Python objects.

This module reads the seven input files in a selected Scenario folder.
It parses input data only; it does not run the simulation or AI algorithms.
"""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Incident, Node, Responder, Road, RoadReport, TrafficObservation


@dataclass
class ScenarioData:
    """Hold all input data required to run one scenario.

    The probability tables remain dictionaries so the Bayesian and HMM
    modules can interpret them independently.
    """

    nodes: dict[str, Node]
    roads: list[Road]
    responders: list[Responder]
    incidents: list[Incident]
    road_reports: list[RoadReport]
    traffic_observations: list[TrafficObservation]
    road_probabilities: dict[str, Any]
    traffic_probabilities: dict[str, Any]


def read_json(file_path: Path) -> Any:
    """Read and decode a JSON input file."""
    with file_path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def read_csv(file_path: Path) -> list[dict[str, str]]:
    """Read a CSV file as a list of dictionaries keyed by column name."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_scenario(scenario_path: str | Path) -> ScenarioData:
    """Load one scenario directory and convert records to model objects.

    Args:
        scenario_path: Directory containing the seven required input files.

    Returns:
        Structured scenario data ready for use by other modules.

    Raises:
        FileNotFoundError: If the directory or an input file is missing.
        ValueError: If the JSON/CSV data contains an invalid value.
        KeyError: If a required field is missing from an input record.
    """
    folder = Path(scenario_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"Scenario directory not found: {folder}")

    graph = read_json(folder / "city_graph.json")

    # A dictionary makes it quick to find nodes by their IDs later.
    nodes = {row["id"]: Node(
        id=row["id"],
        name=row["name"],
        x=float(row["x"]),
        y=float(row["y"]),
        type=row["type"],
    ) for row in graph["nodes"]}

    # Roads are directed: A -> B does not imply B -> A exists.
    roads = [Road(
        from_node=row["from"],
        to_node=row["to"],
        distance=float(row["distance"]),
        road_type=row["road_type"],
        speed=float(row["speed"]),
    ) for row in graph["roads"]]

    responders = [Responder(
        responder_id=row["responder_id"],
        type=row["type"],
        start_location=row["start_location"],
        capabilities={part.strip() for part in row["capabilities"].split(";") if part.strip()},
        availability=row["availability"],
        time_until_available=float(row["time_until_available"]),
    ) for row in read_csv(folder / "responders.csv")]

    incidents = [Incident(
        incident_id=row["incident_id"],
        location=row["location"],
        priority=row["priority"],
        deadline=float(row["deadline"]),
        required_capability=row["required_capability"],
        timestamp=float(row["timestamp"]),
        time_required=float(row["time_required"]),
    ) for row in read_csv(folder / "incidents.csv")]

    road_reports = [RoadReport(
        from_node=row["from"],
        to_node=row["to"],
        weather=row["weather"],
        source=row["source"],
        reported_status=row["reported_status"],
    ) for row in read_csv(folder / "road_reports.csv")]

    traffic_observations = [TrafficObservation(
        observation_nr=int(row["observation_nr"]),
        from_node=row["from"],
        to_node=row["to"],
        traffic_observation=row["traffic_observation"],
    ) for row in read_csv(folder / "observed_traffic.csv")]

    return ScenarioData(
        nodes=nodes,
        roads=roads,
        responders=responders,
        incidents=incidents,
        road_reports=road_reports,
        traffic_observations=traffic_observations,
        road_probabilities=read_json(folder / "road_probabilities.json"),
        traffic_probabilities=read_json(folder / "traffic_probabilities.json"),
    )
