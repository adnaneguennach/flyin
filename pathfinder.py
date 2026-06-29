import heapq
from typing import Dict, List, Optional, Tuple
from models.graph import Graph
from models.zone import Zone, ZoneType

ZONE_COST = {
	ZoneType.NORMAL: 1,
	ZoneType.PRIORITY: 1,
	ZoneType.RESTRICTED: 2,
}


class Pathfinder:
	def __init__(self, graph: Graph) -> None:
		self.graph = graph
		self.reservations: Dict[int, Dict[str, int]] = {}

	def cost_of(self, zone: Zone) -> int:
		return ZONE_COST.get(zone.zone_type, -1)

	def is_free(self, zone: Zone, turn: int) -> bool:
		if zone == self.graph.start or zone == self.graph.end:
			return True
		used = self.reservations.get(turn, {}).get(zone.name, 0)
		return used < zone.max_drones

	def reserve(self, schedule: List[Tuple[Zone, int]]) -> None:
		for zone, turn in schedule:
			if zone == self.graph.start or zone == self.graph.end:
				continue
			if turn not in self.reservations:
				self.reservations[turn] = {}
			self.reservations[turn][zone.name] = \
				self.reservations[turn].get(zone.name, 0) + 1

	def dijkstra(self, start: Zone, end: Zone) -> Optional[List[Tuple[Zone, int]]]:
		dist: Dict[Tuple[str, int], float] = {}
		parent: Dict[Tuple[str, int], Optional[Tuple[str, int]]] = {}
		init = (start.name, 0)
		dist[init] = 0
		parent[init] = None
		queue: List[Tuple[float, str, int]] = [(0.0, start.name, 0)]

		while queue:
			cost, name, turn = heapq.heappop(queue)
			state = (name, turn)
			if dist.get(state, float("inf")) < cost:
				continue
			if name == end.name:
				return self.rebuild(parent, state)

			zone = self.graph.zones[name]

			# wait at current zone
			if self.is_free(zone, turn + 1):
				w_state = (name, turn + 1)
				w_cost = cost + 1
				if w_cost < dist.get(w_state, float("inf")):
					dist[w_state] = w_cost
					parent[w_state] = state
					heapq.heappush(queue, (w_cost, name, turn + 1))

			for neighbor in self.graph.get_neighbors(name):
				step = self.cost_of(neighbor)
				if step == -1:
					continue
				next_turn = turn + step
				if not self.is_free(neighbor, next_turn):
					continue
				n_state = (neighbor.name, next_turn)
				n_cost = cost + step
				if n_cost < dist.get(n_state, float("inf")):
					dist[n_state] = n_cost
					parent[n_state] = state
					heapq.heappush(queue, (n_cost, neighbor.name, next_turn))

		return None

	def rebuild(
		self,
		parent: Dict[Tuple[str, int], Optional[Tuple[str, int]]],
		end_state: Tuple[str, int]
	) -> List[Tuple[Zone, int]]:
		schedule: List[Tuple[Zone, int]] = []
		current: Optional[Tuple[str, int]] = end_state
		while current is not None:
			zone_name, turn = current
			schedule.append((self.graph.zones[zone_name], turn))
			current = parent[current]
		schedule.reverse()
		return schedule

	def plan_all(self, start: Zone, end: Zone, nb_drones: int) -> List[List[Tuple[Zone, int]]]:
		schedules: List[List[Tuple[Zone, int]]] = []
		for i in range(nb_drones):
			schedule = self.dijkstra(start, end)
			if schedule is None:
				raise ValueError(f"no path for drone {i + 1}")
			self.reserve(schedule)
			schedules.append(schedule)
		return schedules