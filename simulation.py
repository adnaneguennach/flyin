from typing import List, Tuple
from models.graph import Graph
from models.zone import Zone
from pathfinder import Pathfinder
from drone import Drone


class Simulation:
	def __init__(self, graph: Graph) -> None:
		self.graph = graph
		self.pathfinder = Pathfinder(graph)
		self.drones: List[Drone] = []
		self.turn: int = 0

	def setup(self) -> None:
		assert self.graph.start is not None and self.graph.end is not None
		schedules = self.pathfinder.plan_all(
			self.graph.start, self.graph.end, self.graph.nb_drones
		)
		for i, schedule in enumerate(schedules):
			self.drones.append(Drone(i + 1, schedule))

	def play_turn(self) -> List[str]:
		moves: List[str] = []
		for drone in self.drones:
			if drone.delivered:
				continue
			nxt = drone.next()
			if nxt is None:
				continue
			curr_zone, curr_turn = drone.curr()
			next_zone, next_turn = nxt
			cost = next_turn - curr_turn

			if next_zone.name == curr_zone.name:
				if self.turn == next_turn:
					drone.step += 1

			elif cost == 2 and self.turn == curr_turn + 1:
				moves.append(f"D{drone.id}-{curr_zone.name}-{next_zone.name}")

			elif self.turn == next_turn:
				drone.zone = next_zone
				drone.step += 1
				moves.append(f"D{drone.id}-{next_zone.name}")
				if drone.zone == self.graph.end:
					drone.delivered = True

		return moves

	def run(self) -> None:
		self.setup()
		while not all(d.delivered for d in self.drones):
			self.turn += 1
			moves = self.play_turn()
			if moves:
				print(" ".join(moves))
		print(f"\ntotal turns: {self.turn}")