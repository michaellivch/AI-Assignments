"""Unit tests for the Emergency Response System data models.

Tests object creation, road travel-time calculations,
responder capabilities, immutability, and edge cases.
"""

from dataclasses import FrozenInstanceError, replace

import pytest

from src.models import (
    Node,
    Road,
    Responder,
    Incident,
    RoadReport,
    TrafficObservation,
)


# ============================================================
# 1. TEST NODE
# ============================================================

def test_node_creation():
    """Verify that a Node stores its attributes correctly."""
    node = Node(
        id="N1",
        name="City Center",
        x=100.0,
        y=200.0,
        type="normal",
    )

    assert node.id == "N1"
    assert node.name == "City Center"
    assert node.x == 100.0
    assert node.y == 200.0
    assert node.type == "normal"


def test_node_immutable():
    """A frozen Node should not allow attribute changes."""
    node = Node("N1", "City Center", 100.0, 200.0, "normal")

    with pytest.raises(FrozenInstanceError):
        node.x = 300.0


# ============================================================
# 2. TEST ROAD
# ============================================================

def test_road_creation():
    """Verify that a Road stores its attributes correctly."""
    road = Road(
        from_node="N1",
        to_node="N2",
        distance=300.0,
        road_type="urban",
        speed=15.0,
    )

    assert road.from_node == "N1"
    assert road.to_node == "N2"
    assert road.distance == 300.0
    assert road.road_type == "urban"
    assert road.speed == 15.0


@pytest.mark.parametrize(
    "distance, speed, expected_time",
    [
        (300.0, 15.0, 20.0),
        (100.0, 10.0, 10.0),
        (150.0, 5.0, 30.0),
        (0.0, 10.0, 0.0),
    ],
)
def test_normal_travel_time(distance, speed, expected_time):
    """Travel time should equal distance divided by speed."""
    road = Road("N1", "N2", distance, "urban", speed)

    assert road.normal_travel_time() == pytest.approx(expected_time)


@pytest.mark.parametrize("speed", [0.0, -5.0])
def test_invalid_road_speed(speed):
    """Zero or negative speed must raise ValueError."""
    road = Road("N1", "N2", 100.0, "urban", speed)

    with pytest.raises(ValueError):
        road.normal_travel_time()


def test_directed_road():
    """A Road should preserve its specified direction."""
    road = Road("N1", "N2", 100.0, "urban", 10.0)

    assert road.from_node == "N1"
    assert road.to_node == "N2"


def test_road_immutable():
    """A frozen Road should not allow attribute changes."""
    road = Road("N1", "N2", 100.0, "urban", 10.0)

    with pytest.raises(FrozenInstanceError):
        road.distance = 500.0


# ============================================================
# 3. TEST RESPONDER
# ============================================================

@pytest.fixture
def responder():
    """Create a responder supporting medical and rescue incidents."""
    return Responder(
        responder_id="R1",
        type="ambulance",
        start_location="N1",
        capabilities={"medical", "rescue"},
        availability="available",
        time_until_available=0.0,
    )


@pytest.fixture
def incident():
    """Create an incident requiring medical assistance."""
    return Incident(
        incident_id="I1",
        location="N2",
        priority="high",
        deadline=100.0,
        required_capability="medical",
        timestamp=10.0,
        time_required=30.0,
    )


def test_responder_creation(responder):
    """Verify that a responder stores its attributes correctly."""
    assert responder.responder_id == "R1"
    assert responder.type == "ambulance"
    assert responder.start_location == "N1"
    assert responder.capabilities == {"medical", "rescue"}
    assert responder.availability == "available"
    assert responder.time_until_available == 0.0


def test_responder_can_handle(responder, incident):
    """A responder should accept incidents matching its capabilities."""
    assert responder.can_handle(incident) is True


def test_responder_cannot_handle(responder, incident):
    """A responder should reject unsupported capabilities."""
    fire_incident = replace(
        incident,
        required_capability="fire",
    )

    assert responder.can_handle(fire_incident) is False


def test_multiple_capabilities(responder, incident):
    """A responder should support any capability in its set."""
    rescue_incident = replace(
        incident,
        required_capability="rescue",
    )

    assert responder.can_handle(rescue_incident) is True


def test_empty_capabilities(responder, incident):
    """A responder without capabilities cannot handle an incident."""
    responder.capabilities = set()

    assert responder.can_handle(incident) is False


def test_responder_availability_mutable(responder):
    """Responder availability must be updateable during simulation."""
    responder.availability = "busy"
    responder.time_until_available = 50.0

    assert responder.availability == "busy"
    assert responder.time_until_available == 50.0


# ============================================================
# 4. TEST INCIDENT
# ============================================================

def test_incident_creation(incident):
    """Verify that an Incident stores its attributes correctly."""
    assert incident.incident_id == "I1"
    assert incident.location == "N2"
    assert incident.priority == "high"
    assert incident.deadline == 100.0
    assert incident.required_capability == "medical"
    assert incident.timestamp == 10.0
    assert incident.time_required == 30.0


def test_incident_immutable(incident):
    """A frozen Incident should not allow attribute changes."""
    with pytest.raises(FrozenInstanceError):
        incident.deadline = 200.0


# ============================================================
# 5. TEST ROAD REPORT
# ============================================================

def test_road_report_creation():
    """Verify that a RoadReport stores its observation correctly."""
    report = RoadReport(
        from_node="N1",
        to_node="N2",
        weather="rain",
        source="citizen",
        reported_status="blocked",
    )

    assert report.from_node == "N1"
    assert report.to_node == "N2"
    assert report.weather == "rain"
    assert report.source == "citizen"
    assert report.reported_status == "blocked"


def test_road_report_immutable():
    """A frozen RoadReport should not allow attribute changes."""
    report = RoadReport(
        "N1", "N2", "rain", "citizen", "blocked"
    )

    with pytest.raises(FrozenInstanceError):
        report.reported_status = "open"


# ============================================================
# 6. TEST TRAFFIC OBSERVATION
# ============================================================

def test_traffic_observation_creation():
    """Verify that a TrafficObservation stores its values correctly."""
    observation = TrafficObservation(
        observation_nr=1,
        from_node="N1",
        to_node="N2",
        traffic_observation="high",
    )

    assert observation.observation_nr == 1
    assert observation.from_node == "N1"
    assert observation.to_node == "N2"
    assert observation.traffic_observation == "high"


def test_traffic_observation_immutable():
    """A frozen TrafficObservation should not allow changes."""
    observation = TrafficObservation(
        1, "N1", "N2", "high"
    )

    with pytest.raises(FrozenInstanceError):
        observation.traffic_observation = "low"
