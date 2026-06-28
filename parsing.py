from models.graph import Graph
from models.zone import Zone, ZoneType
from models.connection import Connection

first_line = True
dict_flags = {
    "nb" : 0,
    "start" : 0,
    "end" : 0
}

with open("test.txt", "r") as file:
    for line_num, raw_line in enumerate(file, start=1):
        line = raw_line.strip()
        if line.startswith("#") or not line:
            continue

        if first_line:
            first_line = False
            if not line.startswith("nb_drones"):
                print(f"First non comment line gotta be nb drones")
                break
        
        if dict_flags["nb"] != 0:
            exit()

        if "nb_drones" in line and dict_flags["nb"] == 0 :
            dict_flags["nb"] = 1
            nb_drones_arr = line.strip().split(":")
            if (nb_drones_arr[0] != "nb_drones"):
                print("wrong naming key")
                break
            try:
                nb_drones = int(nb_drones_arr[1])
                if nb_drones <= 0:
                    raise ValueError
                print(nb_drones)
            except ValueError:
                print("SHOULD BE A VALID positive integer")


        elif "start_hub" in line :
            sh = line.split(":")
            name, x, y = sh[1].strip().split()
            print(name, x, y)



class Parser:
    def __innit__(self, nbr_drones, )