"""Data models for the Emergency Response System.

Defines the scenario entities shared by the parser, search algorithms,
inference components, allocation algorithm, and simulator.

This module contains data definitions and small helper methods only.
It does not load scenario files or make allocation decisions.
"""

# @dataclass to avoid writing constructors manually
from dataclasses import dataclass

@dataclass(frozen=True)
class Node:
    """Represent an intersection or location in the city graph.

    Attributes:
        id: Unique node identifier.
        name: Human-readable node name.
        x: Horizontal coordinate from the scenario.
        y: Vertical coordinate from the scenario.
        type: Location category given in the scenario.
    """

    id: str
    name: str
    x: float
    y: float
    type: str


@dataclass(frozen=True)
class Road:
    """Represent a directed road between two nodes.

    Attributes:
        from_node: Identifier of the road's starting node.
        to_node: Identifier of the road's destination node.
        distance: Road length, assumed to be in metres.
        road_type: Road category from the scenario.
        speed: Normal speed, assumed to be in metres per second.
    """

    from_node: str
    to_node: str
    distance: float
    road_type: str
    speed: float

    def normal_travel_time(self) -> float:
        """Calculate travel time under normal road conditions.

        Returns:
            Travel time in seconds, assuming metres and metres/second.

        Raises:
            ValueError: If the speed is zero or negative.
        """
        if self.speed <= 0:
            raise ValueError("Road speed must be positive")
        return self.distance / self.speed


@dataclass
class Responder:
    """Represent an emergency unit that can be assigned to incidents.

    The responder is mutable because its availability can change during
    the simulation.

    Attributes:
        responder_id: Unique responder identifier.
        type: Responder category (e.g., ambulance, police, fire).
        start_location: Node identifier where the responder starts.
        capabilities: Types of incidents the responder can handle.
        availability: Initial availability status from the scenario.
        time_until_available: Initial delay until the responder is available.
    """

    responder_id: str
    type: str
    start_location: str
    capabilities: set[str]
    availability: str
    time_until_available: float

    def can_handle(self, incident: "Incident") -> bool:
        """Check whether this responder has the required capability.

        Args:
            incident: Incident whose capability requirement is checked.

        Returns:
            True if this responder has the required capability.

        Note:
            This only checks capability; availability, travel time,
            and deadlines must be checked by the allocation logic.
        """
        return incident.required_capability in self.capabilities


@dataclass(frozen=True)
class Incident:
    """Represent an emergency that becomes known at its timestamp.

    Attributes:
        incident_id: Unique incident identifier.
        location: Node identifier of the emergency location.
        priority: Priority level from the scenario.
        deadline: Absolute simulation time by which a responder must arrive.
        required_capability: Capability needed to handle the incident.
        timestamp: Simulation time when the incident is reported.
        time_required: Time needed to handle the incident after arrival.
    """

    incident_id: str
    location: str
    priority: str
    deadline: float
    required_capability: str
    timestamp: float
    time_required: float


@dataclass(frozen=True)
class RoadReport:
    """Represent a potentially noisy report about one road.

    Attributes:
        from_node: Identifier of the road's starting node.
        to_node: Identifier of the road's destination node.
        weather: Weather context included in the report.
        source: Source of the road report.
        reported_status: Reported, not necessarily actual, road condition.
    """

    from_node: str
    to_node: str
    weather: str
    source: str
    reported_status: str


@dataclass(frozen=True)
class TrafficObservation:
    """Represent one traffic observation for a road.

    Attributes:
        observation_nr: Observation sequence number from the scenario.
        from_node: Identifier of the road's starting node.
        to_node: Identifier of the road's destination node.
        traffic_observation: Observed traffic category used by the HMM.
    """

    observation_nr: int
    from_node: str
    to_node: str
    traffic_observation: str
