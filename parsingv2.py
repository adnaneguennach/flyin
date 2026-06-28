from models.graph import Graph
from models.connection import Connection
from typing import List, Dict, Optional
from models.zone import Zone, ZoneType


class Parser:
    first_line = True
    def __init__(self):
        pass
        
    def main_parser(self, file : str) -> Graph:
        nb_drones_seen = False
        start_hub_seen = False
        end_hub_seen = False
        seen_coords: set[tuple[int, int]] = set()
        seen_connections: set[frozenset[str]] = set()
        names: set[str] = set()
        zones : Dict[str, Zone] = dict()

        with open(file, "r") as file:
            for line_num, raw_line in enumerate(file, start= 1):
                line = raw_line.strip()
                if line.startswith("#") or not line:
                    continue
                key, value = line.split(":")
                if self.first_line:
                    self.first_line = False
                    if key.strip() != "nb_drones":
                        raise ValueError(f"Line {line_num} nb drones aint in first line")
            
                if "nb_drones" == key.strip() and not nb_drones_seen:
                    nb_drones_seen = True
                    self.parse_nb_drones(value.strip(), line_num)
                elif "nb_drones" == key.strip() and nb_drones_seen:
                    raise ValueError(f"Line {line_num} Duplicate key")
                
                if "start_hub" == key.strip() and not start_hub_seen:
                    start_hub_seen = True
                    zone = self.parse_hub(value.strip(), line_num, seen_coords, names)
                    zones[zone.get_name()] = zone

                if "hub" == key.strip() and start_hub_seen:
                    zone = self.parse_hub(value.strip(), line_num, seen_coords, names)
                    zones[zone.get_name()] = zone
                elif "hub" == key.strip() and not start_hub_seen:
                    raise ValueError("missing start")
                
                if "end_hub" == key.strip() and not end_hub_seen:
                    end_hub_seen = True
                    zone = self.parse_hub(value.strip(), line_num, seen_coords, names)
                    zones[zone.get_name()] = zone

                if "connection" == key.strip():
                    self.parse_connection(value.strip(), line_num, seen_connections, zones)
                
    
    def parse_nb_drones(self, line : str, line_num : int) -> int:
        try:
            nb_drones = int(line)
            print("inside parse nb drones", nb_drones)
            return nb_drones
        except ValueError:
            raise ValueError(f"Line {line_num}")
    
    def parse_metadata(self, metadata : str, line_num : int) -> Dict:
        metadata_dict = dict()
        VALID_KEYS = {"color","max_drones","zone"}
        VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}
        metadata_arr = metadata.split(" ")
        print(metadata_arr)
        for element in metadata_arr:
            key, value = element.split("=")
            if key not in VALID_KEYS:
                raise ValueError(f"Line {line_num}: Not a valid key")
            if key == "max_drones" and int(value) < 1:
                raise ValueError(f"Line {line_num}: Max drones need to be positive")
            elif key == "zone" and value not in VALID_ZONE_TYPES:
                raise ValueError(f"Line {line_num}: zone type aint valid")
            metadata_dict[key] = value
        print(metadata_dict)
        return metadata_dict
        

    def parse_hub(self, line : str, line_num : int, seen_coords : set[tuple[int, int]], names : set[str]) -> Zone:
        line = line.split("#")[0].strip()
        first_line_split = line.split("[")
        value_arr = first_line_split[0].split()
        if len(value_arr) < 3:
            raise ValueError(f"Line : {line_num} wrong format")

        if len(value_arr) == 3:
            if (len(value_arr) == 3) and not first_line_split[1]:
                name, x, y = value_arr[0], value_arr[1], value_arr[2]
                if (x,y) in seen_coords:
                    raise ValueError(f"Duplicate Coordinates")
                if name in names:
                    raise ValueError(f"Duplicate Names")
                names.add(name)
                seen_coords.add((x,y))
            else:
                name, x, y, metadata = value_arr[0], value_arr[1], value_arr[2], first_line_split[1].strip("]")
                if (x,y) in seen_coords:
                    raise ValueError(f"Duplicate Coordinates")
                if name in names:
                    raise ValueError(f"Duplicate Names")
                names.add(name)
                seen_coords.add((x,y))
                metadata_dict = self.parse_metadata(metadata, line_num)
                zone_type = metadata_dict.get("zone", ZoneType.NORMAL)
                color = metadata_dict.get("color", "")
                max_drones = metadata_dict.get("max_drones", 1)


            if "-" in name:
                raise ValueError(f"Line {line_num}: invalid name format")
            try:
                int_x = int(x)
                int_y = int(y)
                return Zone(name, x, y, zone_type, max_drones, color)
            except ValueError:
                raise ValueError(f"Line {line_num}: invalid integer format x, y")
        else:
            raise ValueError(f"Line {line_num}: wrong formatting")
                
    def parse_connection(self ,line : str, line_num : int, seen_connections : set[frozenset[str]], zones) -> Connection:
        zone1, zone2 = line.strip().split("-")
        pair = frozenset({zone1, zone2})
        if pair in seen_connections:
            raise ValueError(f"Line {line_num}:Duplicate connection")
        seen_connections.add(pair)
        try:
            print(Connection(zones[zone1], zones[zone2]))
        except KeyError as e:
            raise ValueError(f"Line {line_num}: unknown zone {e}") from None


file = "test.txt"
obj = Parser()
obj.main_parser(file)