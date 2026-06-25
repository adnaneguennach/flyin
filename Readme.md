# Fly-in

*This project has been created as part of the 42 curriculum.*

## Description

A drone routing simulator that moves a fleet of drones from a start zone to an end zone across a graph network, in the fewest possible simulation turns.

## Zone Types

| Type | Description | Cost |
|---|---|---|
| `normal` | Regular zone | 1 turn |
| `priority` | Fast lane, preferred by pathfinder | 1 turn |
| `restricted` | Dangerous/slow area | 2 turns |
| `blocked` | Impassable | - |

By default a zone holds only 1 drone at a time (overridable with `max_drones`).

```
[start] → zone → zone → zone → [end]
                  ↑
         drones compete for space here
```

## Progress

### Models (data layer)
- `models/zone.py` — `ZoneType` enum + `Zone` class (name, coords, type, capacity, color)
- `models/connection.py` — `Connection` class (bidirectional link between two zones, max capacity)
- `models/graph.py` — `Graph` class (holds all zones + connections, provides neighbor lookup)

### In progress
- `parser.py` — reads map file and builds the Graph
- `drone.py` — drone state tracking
- `simulation.py` — turn-by-turn engine
- `pathfinder.py` — routing algorithm
- `visualizer.py` — terminal/graphical output
