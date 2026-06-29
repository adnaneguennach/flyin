from typing import List, Optional, Tuple
from models.zone import Zone


class Drone:
	def __init__(self, drone_id: int, schedule: List[Tuple[Zone, int]]) -> None:
		self.id = drone_id
		self.zone: Zone = schedule[0][0]
		self.schedule: List[Tuple[Zone, int]] = schedule
		self.step: int = 0
		self.delivered: bool = False

	def curr(self) -> Tuple[Zone, int]:
		return self.schedule[self.step]

	def next(self) -> Optional[Tuple[Zone, int]]:
		if self.step + 1 >= len(self.schedule):
			return None
		return self.schedule[self.step + 1]

	def __repr__(self) -> str:
		return f"D{self.id}"