from models.graph import Graph
from models.connection import Connection
from typing import List, Dict, Optional
from models.zone import Zone, ZoneType
import re


class Parser:
	def __init__(self) -> None:
		pass

	def main_parser(self, file: str) -> Graph:
		nb_drones_seen = False
		start_hub_seen = False
		end_hub_seen = False
		first_line = True
		seen_coords: set[tuple[int, int]] = set()
		seen_connections: set[frozenset[str]] = set()
		names: set[str] = set()
		zones: Dict[str, Zone] = dict()
		graph = Graph()

		with open(file, "r") as f:
			for line_num, raw_line in enumerate(f, start=1):
				line = raw_line.split("#")[0].strip()
				if not line:
					continue
				key, _, value = line.partition(":")
				key = key.strip()
				value = value.strip()

				if first_line:
					first_line = False
					if key != "nb_drones":
						raise ValueError(f"Line {line_num}: nb_drones must be first line")

				if key == "nb_drones" and not nb_drones_seen:
					nb_drones_seen = True
					graph.nb_drones = self.parse_nb_drones(value, line_num)
				elif key == "nb_drones" and nb_drones_seen:
					raise ValueError(f"Line {line_num}: duplicate nb_drones")

				elif key == "start_hub" and not start_hub_seen:
					start_hub_seen = True
					zone = self.parse_hub(value, line_num, seen_coords, names)
					zones[zone.name] = zone
					graph.add_zone(zone)
					graph.start = zone

				elif key == "hub":
					zone = self.parse_hub(value, line_num, seen_coords, names)
					zones[zone.name] = zone
					graph.add_zone(zone)

				elif key == "end_hub" and not end_hub_seen:
					end_hub_seen = True
					zone = self.parse_hub(value, line_num, seen_coords, names)
					zones[zone.name] = zone
					graph.add_zone(zone)
					graph.end = zone

				elif key == "connection":
					conn = self.parse_connection(value, line_num, seen_connections, zones)
					graph.add_connection(conn)

		if not start_hub_seen:
			raise ValueError("missing start_hub")
		if not end_hub_seen:
			raise ValueError("missing end_hub")

		if graph.start and graph.start.max_drones_set and graph.start.max_drones < graph.nb_drones:
			raise ValueError(
				f"start_hub max_drones ({graph.start.max_drones}) "
				f"must be >= nb_drones ({graph.nb_drones})"
			)
		if graph.end and graph.end.max_drones_set and graph.end.max_drones < graph.nb_drones:
			raise ValueError(
				f"end_hub max_drones ({graph.end.max_drones}) "
				f"must be >= nb_drones ({graph.nb_drones})"
			)
		
		return graph

	def parse_nb_drones(self, line: str, line_num: int) -> int:
		try:
			nb_drones = int(line)
			if nb_drones < 1:
				raise ValueError()
			return nb_drones
		except ValueError:
			raise ValueError(f"Line {line_num}: nb_drones must be a positive integer")

	def validate_metadata_keys(self, keys: set[str], valid_keys: set[str], line_num: int) -> None:
		for key in keys:
			if key not in valid_keys:
				raise ValueError(f"Line {line_num}: not a valid key '{key}'")

	def parse_metadata(self, metadata: str, line_num: int, valid_keys: set[str]) -> Dict[str, str]:
		metadata_dict: Dict[str, str] = dict()
		VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
		pairs_metadata = re.findall(r'(\w+)\s*=\s*(\w+)', metadata)
		for key, value in pairs_metadata:
			self.validate_metadata_keys({key}, valid_keys, line_num)
			if key == "max_drones" and (not value.isdigit() or int(value) < 1):
				raise ValueError(f"Line {line_num}: max_drones must be a positive integer")
			if key == "max_link_capacity" and (not value.isdigit() or int(value) < 1):
				raise ValueError(f"Line {line_num}: max_link_capacity must be a positive integer")
			if key == "zone" and value not in VALID_ZONE_TYPES:
				raise ValueError(f"Line {line_num}: zone type '{value}' is not valid")
			metadata_dict[key] = value
		return metadata_dict

	def parse_hub(
		self,
		line: str,
		line_num: int,
		seen_coords: set[tuple[int, int]],
		names: set[str]
	) -> Zone:
		bracket_content = re.search(r'\[.*\]', line)
		if bracket_content:
			raw = bracket_content.group()
			if not re.fullmatch(r'\[[^\[\]]*\]', raw):
				raise ValueError(f"Line {line_num}: invalid metadata block")

		first_line_split = line.split(maxsplit=3)
		value_arr = first_line_split[:3]

		if len(value_arr) < 3:
			raise ValueError(f"Line {line_num}: wrong format")

		name, x, y = value_arr[0], value_arr[1], value_arr[2]

		if "-" in name:
			raise ValueError(f"Line {line_num}: zone name cannot contain dashes")

		try:
			int_x = int(x)
			int_y = int(y)
		except ValueError:
			raise ValueError(f"Line {line_num}: x and y must be integers")

		if (int_x, int_y) in seen_coords:
			raise ValueError(f"Line {line_num}: duplicate coordinates ({int_x}, {int_y})")
		if name in names:
			raise ValueError(f"Line {line_num}: duplicate zone name '{name}'")

		names.add(name)
		seen_coords.add((int_x, int_y))

		zone_type = ZoneType.NORMAL
		color = ""
		max_drones = 1

		max_drones = None

		if len(first_line_split) == 4:
			metadata_raw = first_line_split[3].strip("[]")
			metadata_dict = self.parse_metadata(metadata_raw, line_num, {"color", "max_drones", "zone"})
			if "zone" in metadata_dict:
				zone_type = ZoneType(metadata_dict["zone"])
			if "color" in metadata_dict:
				color = metadata_dict["color"]
			if "max_drones" in metadata_dict:
				max_drones = int(metadata_dict["max_drones"])

		return Zone(name, int_x, int_y, zone_type, max_drones or 1, color, max_drones is not None)

	def parse_connection(
		self,
		line: str,
		line_num: int,
		seen_connections: set[frozenset[str]],
		zones: Dict[str, Zone]
	) -> Connection:
		bracket_content = re.search(r'\[.*\]', line)
		if bracket_content:
			raw = bracket_content.group()
			if not re.fullmatch(r'\[[^\[\]]*\]', raw):
				raise ValueError(f"Line {line_num}: invalid metadata block")

		parts = line.strip().split(maxsplit=1)
		zone1, zone2 = parts[0].strip().split("-")
		metadata_dict: Dict[str, str] = dict()

		if len(parts) == 2:
			metadata = parts[1].strip("[]")
			metadata_dict = self.parse_metadata(metadata, line_num, {"max_link_capacity"})

		pair = frozenset({zone1, zone2})
		if pair in seen_connections:
			raise ValueError(f"Line {line_num}: duplicate connection")
		seen_connections.add(pair)

		try:
			max_link_capacity = int(metadata_dict.get("max_link_capacity", "1"))
			return Connection(zones[zone1], zones[zone2], max_link_capacity)
		except KeyError as e:
			raise ValueError(f"Line {line_num}: unknown zone {e}") from None
