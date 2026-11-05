"""Shortest-path routing for the Emergency Response System.

Uniform Cost Search (UCS), equivalent to Dijkstra's algorithm on this
finite directed graph, finds a minimum estimated travel-time route.

Road weights are fixed during one call. Other modules may supply estimated
weights based on uncertain road status and traffic observations.
"""

from collections import defaultdict
import heapq
import math
from typing import Mapping

from .models import Road

# Directed road identifier: (source node, destination node).
RoadKey = tuple[str, str]


def find_shortest_path(
    roads: list[Road],
    start: str,
    goal: str,
    road_costs: Mapping[RoadKey, float] | None = None,
) -> tuple[list[str], float]:
    """Find the minimum-cost route between two nodes using UCS/Dijkstra.

    Args:
        roads: Directed roads forming the city graph.
        start: Start node identifier.
        goal: Destination node identifier.
        road_costs: Optional estimated travel times in seconds, keyed by
            ``(from_node, to_node)``. Omitted roads use normal travel time.
            An infinite cost excludes that directed road (e.g., blocked).

    Returns:
        ``(path, travel_time_seconds)`` where the path includes both
        endpoints. If no route exists, returns ``([], math.inf)``.
        For start == goal, returns ``([start], 0.0)``.

    Raises:
        ValueError: For invalid road distances/speeds, negative or NaN
            costs, or duplicate directed edges.
        KeyError: For a start or goal not present in the graph, or an
            override referring to a nonexistent road.

    Notes:
        This algorithm optimizes the given estimated costs, not unknown
        actual travel times. Road costs must be fixed and nonnegative for
        the duration of the search. It does not enforce incident deadlines.
    """
    overrides = {} if road_costs is None else dict(road_costs)
    adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
    nodes: set[str] = set()
    edge_keys: set[RoadKey] = set()

    for road in roads:
        key = (road.from_node, road.to_node)
        if key in edge_keys:
            raise ValueError(f"Duplicate directed road: {key}")
        edge_keys.add(key)
        nodes.update(key)

        # Even an overridden edge must have valid base data.
        if not math.isfinite(road.distance) or road.distance < 0:
            raise ValueError(f"Invalid road distance: {key}")
        normal_cost = road.normal_travel_time()
        if not math.isfinite(normal_cost):
            raise ValueError(f"Invalid normal travel time: {key}")

        cost = overrides.get(key, normal_cost)
        # +infinity is the explicit marker for a road that cannot be used.
        if math.isnan(cost) or cost < 0 or cost == -math.inf:
            raise ValueError(f"Invalid travel cost for road {key}: {cost}")
        if math.isfinite(cost):
            adjacency[road.from_node].append((road.to_node, cost))

    for key, cost in overrides.items():
        if key not in edge_keys:
            raise KeyError(f"Cost override refers to unknown road: {key}")
        if not isinstance(cost, (int, float)):
            raise ValueError(f"Road cost must be numeric: {key}")

    if start not in nodes:
        raise KeyError(f"Unknown start node: {start}")
    if goal not in nodes:
        raise KeyError(f"Unknown destination node: {goal}")
    if start == goal:
        return [start], 0.0

    # The priority queue always expands the lowest cumulative-cost path.
    frontier: list[tuple[float, str]] = [(0.0, start)]
    best_cost = {start: 0.0}
    predecessor: dict[str, str] = {}

    while frontier:
        current_cost, current = heapq.heappop(frontier)

        # Old queue entries become stale when a cheaper route is found.
        if current_cost > best_cost[current]:
            continue

        # UCS is optimal when a goal is popped, not merely discovered.
        if current == goal:
            path = [goal]
            while path[-1] != start:
                path.append(predecessor[path[-1]])
            path.reverse()
            return path, current_cost

        for neighbor, step_cost in adjacency[current]:
            new_cost = current_cost + step_cost
            if new_cost < best_cost.get(neighbor, math.inf):
                best_cost[neighbor] = new_cost
                predecessor[neighbor] = current
                heapq.heappush(frontier, (new_cost, neighbor))

    # No usable directed path connects start to goal.
    return [], math.inf
