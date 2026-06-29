import sys
import subprocess
import tempfile
import pygame
from typing import Dict, List, Tuple, Optional

pygame.init()

W, H = 1400, 800
FPS = 60
NODE_R = 22
FONT = pygame.font.SysFont("monospace", 11)
FONT_SM = pygame.font.SysFont("monospace", 9)
FONT_LG = pygame.font.SysFont("monospace", 16, bold=True)

BG        = (15, 15, 20)
EDGE_COL  = (50, 50, 65)
TEXT_COL  = (220, 220, 220)
MUTED     = (100, 100, 120)
PANEL_BG  = (25, 25, 35)

ZONE_COLORS = {
    "start":      (50, 200, 100),
    "end":        (180, 80, 220),
    "normal":     (60, 100, 160),
    "restricted": (200, 140, 30),
    "priority":   (30, 180, 180),
    "blocked":    (60, 60, 70),
}

DRONE_PALETTE = [
    (255, 80,  80),
    (80,  160, 255),
    (80,  230, 120),
    (255, 200, 50),
    (220, 80,  220),
    (80,  220, 220),
    (255, 140, 50),
    (160, 255, 80),
    (255, 100, 160),
    (100, 200, 255),
]


class Zone:
    def __init__(self, name: str, x: int, y: int, zone_type: str, max_drones: int) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.px = 0
        self.py = 0


def parse_map(path: str):
    zones: Dict[str, Zone] = {}
    connections: List[Tuple[str, str]] = []
    start_name = ""
    end_name = ""

    with open(path) as f:
        for raw in f:
            line = raw.split("#")[0].strip()
            if not line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()

            if key in ("start_hub", "hub", "end_hub"):
                parts = value.split(maxsplit=3)
                name, x, y = parts[0], int(parts[1]), int(parts[2])
                zone_type = "normal"
                max_drones = 1
                if len(parts) == 4:
                    for kv in parts[3].strip("[]").split():
                        k, _, v = kv.partition("=")
                        if k == "zone":
                            zone_type = v
                        if k == "max_drones":
                            max_drones = int(v)
                if key == "start_hub":
                    zone_type = "start"
                    start_name = name
                if key == "end_hub":
                    zone_type = "end"
                    end_name = name
                zones[name] = Zone(name, x, y, zone_type, max_drones)

            elif key == "connection":
                parts = value.strip().split(maxsplit=1)
                a, b = parts[0].split("-")
                connections.append((a, b))

    return zones, connections, start_name, end_name


def parse_output(path: str) -> List[Dict[str, str]]:
    turns = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if any(line.startswith(p) for p in ("total", "Graph", "path", "drone")):
                continue
            turn: Dict[str, str] = {}
            for move in line.split():
                parts = move.split("-")
                drone_id = parts[0]
                if not drone_id.startswith("D"):
                    continue
                if len(parts) == 2:
                    turn[drone_id] = parts[1]
                elif len(parts) == 3:
                    turn[drone_id] = f"{parts[1]}->{parts[2]}"
            if turn:
                turns.append(turn)
    return turns


def layout_zones(zones: Dict[str, Zone], margin: int = 80, panel_w: int = 300) -> None:
    usable_w = W - panel_w - margin * 2
    usable_h = H - margin * 2
    xs = [z.x for z in zones.values()]
    ys = [z.y for z in zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    rx = max_x - min_x or 1
    ry = max_y - min_y or 1
    for z in zones.values():
        z.px = margin + int((z.x - min_x) / rx * usable_w)
        z.py = margin + int((max_y - z.y) / ry * usable_h)


def drone_color(drone_id: str) -> Tuple[int, int, int]:
    num = int(drone_id[1:]) - 1
    return DRONE_PALETTE[num % len(DRONE_PALETTE)]


def draw_scene(
    screen: pygame.Surface,
    zones: Dict[str, Zone],
    connections: List[Tuple[str, str]],
    zone_drones: Dict[str, List[str]],
    turn_num: int,
    total_turns: int,
    moves: Dict[str, str],
    paused: bool,
    speed: float,
) -> None:
    screen.fill(BG)
    panel_x = W - 300

    pygame.draw.rect(screen, PANEL_BG, (panel_x, 0, 300, H))

    for a, b in connections:
        if a in zones and b in zones:
            pygame.draw.line(screen, EDGE_COL,
                (zones[a].px, zones[a].py),
                (zones[b].px, zones[b].py), 1)

    for name, zone in zones.items():
        col = ZONE_COLORS.get(zone.zone_type, ZONE_COLORS["normal"])
        drones_here = zone_drones.get(name, [])

        if drones_here:
            outer = tuple(min(255, c + 60) for c in col)
            pygame.draw.circle(screen, outer, (zone.px, zone.py), NODE_R + 4)

        pygame.draw.circle(screen, col, (zone.px, zone.py), NODE_R)
        pygame.draw.circle(screen, tuple(min(255, c + 80) for c in col),
            (zone.px, zone.py), NODE_R, 2)

        label = FONT_SM.render(name[:8], True, TEXT_COL)
        screen.blit(label, (zone.px - label.get_width() // 2, zone.py + NODE_R + 2))

        if drones_here:
            count_txt = FONT.render(str(len(drones_here)), True, (255, 255, 255))
            screen.blit(count_txt, (zone.px - count_txt.get_width() // 2,
                zone.py - count_txt.get_height() // 2))

            for i, did in enumerate(drones_here[:3]):
                dc = drone_color(did)
                dot_x = zone.px + (i - 1) * 10
                dot_y = zone.py - NODE_R - 8
                pygame.draw.circle(screen, dc, (dot_x, dot_y), 4)

    py = 20
    title = FONT_LG.render("drone router", True, TEXT_COL)
    screen.blit(title, (panel_x + 20, py))
    py += 30

    turn_col = (100, 200, 255)
    t_txt = FONT_LG.render(f"turn {turn_num} / {total_turns}", True, turn_col)
    screen.blit(t_txt, (panel_x + 20, py))
    py += 30

    bar_w = 260
    prog = turn_num / total_turns if total_turns else 0
    pygame.draw.rect(screen, (50, 50, 70), (panel_x + 20, py, bar_w, 8), border_radius=4)
    pygame.draw.rect(screen, turn_col, (panel_x + 20, py, int(bar_w * prog), 8), border_radius=4)
    py += 20

    state_txt = "paused" if paused else f"auto  {speed:.1f}s/turn"
    st = FONT.render(state_txt, True, MUTED)
    screen.blit(st, (panel_x + 20, py))
    py += 25

    pygame.draw.line(screen, (50, 50, 70), (panel_x + 10, py), (panel_x + 290, py))
    py += 10

    moves_title = FONT.render("moves this turn:", True, MUTED)
    screen.blit(moves_title, (panel_x + 20, py))
    py += 18

    for did, dest in list(moves.items())[:18]:
        dc = drone_color(did)
        d_surf = FONT.render(did, True, dc)
        screen.blit(d_surf, (panel_x + 20, py))
        arr = FONT.render(f" -> {dest[:16]}", True, TEXT_COL)
        screen.blit(arr, (panel_x + 20 + d_surf.get_width(), py))
        py += 15
        if py > H - 130:
            more = FONT.render(f"... +{len(moves) - 18} more", True, MUTED)
            screen.blit(more, (panel_x + 20, py))
            break

    py = H - 120
    pygame.draw.line(screen, (50, 50, 70), (panel_x + 10, py), (panel_x + 290, py))
    py += 8

    legend = [
        ("start",      ZONE_COLORS["start"]),
        ("end",        ZONE_COLORS["end"]),
        ("normal",     ZONE_COLORS["normal"]),
        ("restricted", ZONE_COLORS["restricted"]),
        ("priority",   ZONE_COLORS["priority"]),
    ]
    for lbl, col in legend:
        pygame.draw.circle(screen, col, (panel_x + 30, py + 5), 6)
        lt = FONT_SM.render(lbl, True, MUTED)
        screen.blit(lt, (panel_x + 42, py))
        py += 16

    controls = [
        "space  pause/resume",
        "right  next turn",
        "left   prev turn",
        "up/dn  speed",
        "r      restart",
        "q      quit",
    ]
    cx, cy = 10, H - len(controls) * 14 - 10
    for ctrl in controls:
        ct = FONT_SM.render(ctrl, True, (70, 70, 90))
        screen.blit(ct, (cx, cy))
        cy += 14

    pygame.display.flip()


def run_sim(map_file: str) -> str:
    print("running simulation...")
    result = subprocess.run(["python3", "main.py"], capture_output=True, text=True)
    out_file = tempfile.mktemp(suffix=".txt")
    with open(out_file, "w") as f:
        f.write(result.stdout)
    return out_file


def main() -> None:
    map_file = sys.argv[1] if len(sys.argv) > 1 else "test.txt"
    sim_output = sys.argv[2] if len(sys.argv) > 2 else None

    if sim_output is None:
        sim_output = run_sim(map_file)

    zones, connections, start_name, end_name = parse_map(map_file)
    turns = parse_output(sim_output)
    layout_zones(zones)

    all_drones: List[str] = sorted(
        {did for turn in turns for did in turn},
        key=lambda d: int(d[1:])
    )

    drone_positions: Dict[str, str] = {d: start_name for d in all_drones}
    history: List[Dict[str, str]] = [dict(drone_positions)]

    for turn_moves in turns:
        for did, dest in turn_moves.items():
            if "->" not in dest:
                drone_positions[did] = dest
        history.append(dict(drone_positions))

    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("drone router visualizer")
    clock = pygame.time.Clock()

    turn_idx = 0
    paused = True
    speed = 0.5
    auto_timer = 0.0

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    paused = not paused
                    auto_timer = 0
                if event.key == pygame.K_RIGHT and turn_idx < len(turns):
                    turn_idx += 1
                    auto_timer = 0
                if event.key == pygame.K_LEFT and turn_idx > 0:
                    turn_idx -= 1
                    auto_timer = 0
                if event.key == pygame.K_r:
                    turn_idx = 0
                    paused = True
                    auto_timer = 0
                if event.key == pygame.K_UP:
                    speed = max(0.1, round(speed - 0.1, 1))
                if event.key == pygame.K_DOWN:
                    speed = min(3.0, round(speed + 0.1, 1))

        if not paused and turn_idx < len(turns):
            auto_timer += dt
            if auto_timer >= speed:
                auto_timer = 0
                turn_idx += 1

        pos = history[min(turn_idx, len(history) - 1)]
        zone_drones: Dict[str, List[str]] = {name: [] for name in zones}
        for did, zname in pos.items():
            if zname in zone_drones:
                zone_drones[zname].append(did)

        current_moves = turns[turn_idx - 1] if 0 < turn_idx <= len(turns) else {}

        draw_scene(
            screen, zones, connections,
            zone_drones,
            turn_idx, len(turns),
            current_moves,
            paused, speed,
        )


if __name__ == "__main__":
    main()