"""
CS0065 - Intelligent Systems
Technical Assessment 1: Random Walk Simulation Using AgentPy (Modified Code)

This program extends the provided random walk code to cover the four
laboratory tasks:

  Task 1 - Track agent paths: every agent records each cell it occupies.
           The paths are drawn as trails in the animation, printed in the
           console, and saved to TA1_agent_paths.csv.
  Task 2 - Change movement rules: the user picks one of three rules.
             [1] Random walk         - the original rule (25% per direction)
             [2] Avoid each other    - never step into a cell another agent is in
             [3] Preferred direction - biased walk toward a chosen direction
  Task 3 - Analyze final positions: final positions are printed, mapped,
           saved to TA1_final_positions.csv, and summarized (centroid,
           spread, quadrant counts, crowding, grid coverage).
  Task 4 - Compare scenarios: two simulations (A and B) are run with
           user-entered parameters and compared side by side.

Libraries needed: agentpy, matplotlib  (pip install agentpy matplotlib)
"""

import csv
import math
import random
from collections import Counter

import agentpy as ap
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# The four possible moves (same four directions as the original code)
DIRECTIONS = {'R': (1, 0), 'L': (-1, 0), 'U': (0, 1), 'D': (0, -1)}
DIRECTION_NAMES = {'R': 'Right', 'L': 'Left', 'U': 'Up', 'D': 'Down'}
RULE_NAMES = {1: 'Random walk', 2: 'Avoid each other', 3: 'Preferred direction'}
PREFERRED_PROB = 0.50     # Rule 3: chance of stepping in the preferred direction
MAX_TABLE_ROWS = 25       # Longest per-agent table printed in the console
LINE = '=' * 78


# ---------------------------------------------------------------------------
# Console input helpers (re-ask until the input is valid)
# ---------------------------------------------------------------------------
def ask_int(prompt, minimum, maximum=None):
    """Ask for a whole number within [minimum, maximum]."""
    while True:
        text = input(prompt).strip()
        try:
            value = int(text)
        except ValueError:
            print("   Invalid input: please enter a whole number.")
            continue
        if value < minimum or (maximum is not None and value > maximum):
            if maximum is None:
                print(f"   Invalid input: the value must be at least {minimum}.")
            else:
                print(f"   Invalid input: the value must be from {minimum} to {maximum}.")
            continue
        return value


def ask_direction(prompt):
    """Ask for one of U, D, L, R (not case sensitive)."""
    while True:
        text = input(prompt).strip().upper()
        if text in DIRECTIONS:
            return text
        print("   Invalid input: please type U, D, L or R.")


def ask_seed():
    """Optional seed so that a run can be reproduced exactly."""
    text = input("Enter random seed (press Enter for a random seed): ").strip()
    if text == '':
        seed = random.randint(1, 999999)
        print(f"   Using random seed: {seed}")
        return seed
    try:
        return int(text)
    except ValueError:
        seed = random.randint(1, 999999)
        print(f"   Not a whole number, using random seed: {seed}")
        return seed


def get_scenario(label, seed):
    """Collect the parameters of one simulation from the console."""
    print(f"\n--- Simulation {label} ---")
    num_agents = ask_int("Enter number of agents: ", 1)
    grid_size = ask_int("Enter grid size (e.g., 10 for 10x10): ", 2)
    num_steps = ask_int("Enter number of steps: ", 1)
    print("Movement rules: [1] Random walk  [2] Avoid each other  [3] Preferred direction")
    rule = ask_int("Choose movement rule (1-3): ", 1, 3)
    preferred = ask_direction("Enter preferred direction (U/D/L/R): ") if rule == 3 else None
    return {
        'label': label,
        'agents': num_agents,
        'grid_size': (grid_size, grid_size),
        'steps': num_steps,          # AgentPy stops the run after this many steps
        'rule': rule,
        'preferred': preferred,
        'seed': seed,                # AgentPy seeds model.random with this value
    }


def direction_key(delta):
    """Turn a move such as (1, 0) into its letter ('R')."""
    for key, value in DIRECTIONS.items():
        if value == delta:
            return key
    return None


def describe(p):
    """One-line description of a parameter set."""
    rule = RULE_NAMES[p['rule']]
    if p['rule'] == 3:
        rule += f" ({DIRECTION_NAMES[p['preferred']]})"
    size = p['grid_size'][0]
    return f"{rule}, {p['agents']} agents, {size}x{size} grid, {p['steps']} steps"


# ---------------------------------------------------------------------------
# Agent Definition
# ---------------------------------------------------------------------------
class RandomWalker(ap.Agent):

    def setup(self):
        self.path = []                              # Task 1: every cell occupied, in order
        self.moves = 0                              # steps where the agent changed cell
        self.stayed = 0                             # steps where the agent could not move
        self.chosen_counts = Counter()              # Task 2: directions picked by the rule
        self.direction_counts = Counter()           # Task 2: directions actually moved

    @property
    def position(self):
        # The AgentPy grid is the single source of truth for every position
        return self.model.grid.positions[self]

    def step(self):
        x, y = self.position
        width, height = self.model.p.grid_size

        if self.model.p.rule == 2:
            new_pos = self.avoid_move(x, y, width, height)
        else:
            if self.model.p.rule == 3:
                dx, dy = self.biased_direction()
            else:
                dx, dy = self.model.random.choice(list(DIRECTIONS.values()))
            self.chosen_counts[direction_key((dx, dy))] += 1
            # Keep agents inside grid (same clamping as the original code)
            new_x = max(0, min(width - 1, x + dx))
            new_y = max(0, min(height - 1, y + dy))
            new_pos = (new_x, new_y)

        # Bookkeeping for the analysis
        if new_pos == (x, y):
            self.stayed += 1
        else:
            self.moves += 1
            self.direction_counts[direction_key((new_pos[0] - x, new_pos[1] - y))] += 1

        self.model.grid.move_to(self, new_pos)
        self.path.append(new_pos)                   # Task 1: record the new cell

    def biased_direction(self):
        """Rule 3: go the preferred way 50% of the time, otherwise pick one
        of the other three directions (about 16.7% each)."""
        preferred = self.model.p.preferred
        if self.model.random.random() < PREFERRED_PROB:
            return DIRECTIONS[preferred]
        others = [delta for key, delta in DIRECTIONS.items() if key != preferred]
        return self.model.random.choice(others)

    def avoid_move(self, x, y, width, height):
        """Rule 2: only consider neighbouring cells that are inside the grid
        and empty. If every neighbouring cell is taken, stay in place."""
        options = []
        for dx, dy in DIRECTIONS.values():
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not self.model.is_occupied((nx, ny)):
                options.append((nx, ny))
        if options:
            choice = self.model.random.choice(options)
            self.chosen_counts[direction_key((choice[0] - x, choice[1] - y))] += 1
            return choice
        return (x, y)


# ---------------------------------------------------------------------------
# Model Definition
# ---------------------------------------------------------------------------
class RandomWalkModel(ap.Model):

    def setup(self):
        width, height = self.p.grid_size

        # Create agents first so their IDs are 1, 2, 3, ...
        self.agents = ap.AgentList(self, self.p.agents, RandomWalker)
        self.grid = ap.Grid(self, self.p.grid_size, torus=False)

        # Initialize random positions: each agent gets its own cell when there
        # is room; if there are more agents than cells, cells must be shared.
        cells = [(x, y) for x in range(width) for y in range(height)]
        if self.p.agents <= len(cells):
            starts = self.random.sample(cells, self.p.agents)
        else:
            starts = [self.random.choice(cells) for _ in range(self.p.agents)]
        self.grid.add_agents(self.agents, positions=starts)
        for agent in self.agents:
            agent.path.append(agent.position)

        # Histories used for the spread-over-time chart (filled in update)
        self.visited = set()
        self.coverage_history = []           # % of cells visited so far
        self.displacement_history = []       # average distance from start
        self.max_stack = 0                   # most agents ever sharing one cell

    def is_occupied(self, pos):
        """True if at least one agent is standing on the cell."""
        return len(self.grid.grid.agents[pos]) > 0

    def step(self):
        # Agents move one at a time in a new random order every step,
        # so no agent always gets the first pick of the free cells.
        order = list(self.agents)
        self.random.shuffle(order)
        for agent in order:
            agent.step()

    def update(self):
        # Runs after setup (t = 0) and after every step
        width, height = self.p.grid_size
        positions = [agent.position for agent in self.agents]
        self.visited.update(positions)
        self.coverage_history.append(100 * len(self.visited) / (width * height))
        distances = [math.dist(agent.path[0], agent.position) for agent in self.agents]
        self.displacement_history.append(sum(distances) / len(distances))
        self.max_stack = max(self.max_stack, max(Counter(positions).values()))


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------
def analyze(model):
    """Summary statistics used in Tasks 2, 3 and 4."""
    width, height = model.p.grid_size
    finals = [agent.position for agent in model.agents]
    n = len(finals)
    xs = [pos[0] for pos in finals]
    ys = [pos[1] for pos in finals]
    cx, cy = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - cx) ** 2 for x in xs) / n)
    sy = math.sqrt(sum((y - cy) ** 2 for y in ys) / n)
    center = ((width - 1) / 2, (height - 1) / 2)

    # Quadrants: x >= half_x is the right half, y >= half_y is the upper half
    half_x, half_y = math.ceil(width / 2), math.ceil(height / 2)
    quadrants = Counter()
    for x, y in finals:
        if x >= half_x and y >= half_y:
            quadrants['Q1'] += 1
        elif x < half_x and y >= half_y:
            quadrants['Q2'] += 1
        elif x < half_x:
            quadrants['Q3'] += 1
        else:
            quadrants['Q4'] += 1

    cell_counts = Counter(finals)
    all_inside = all(0 <= x < width and 0 <= y < height
                     for agent in model.agents for x, y in agent.path)
    directions, chosen = Counter(), Counter()
    for agent in model.agents:
        directions.update(agent.direction_counts)
        chosen.update(agent.chosen_counts)

    return {
        'finals': finals,
        'centroid': (cx, cy),
        'std': (sx, sy),
        'spread': sum(math.dist((cx, cy), pos) for pos in finals) / n,
        'center_dist': sum(math.dist(center, pos) for pos in finals) / n,
        'quadrants': quadrants,
        'border': sum(1 for x, y in finals if x in (0, width - 1) or y in (0, height - 1)),
        'cell_counts': cell_counts,
        'occupied': len(cell_counts),
        'max_cell': max(cell_counts.values()),
        'displacement': model.displacement_history[-1],
        'avg_moves': sum(agent.moves for agent in model.agents) / n,
        'avg_stayed': sum(agent.stayed for agent in model.agents) / n,
        'total_stayed': sum(agent.stayed for agent in model.agents),
        'coverage': model.coverage_history[-1],
        'density': n / (width * height),
        'all_inside': all_inside,
        'directions': directions,
        'chosen': chosen,
        'max_stack': model.max_stack,
    }


def fmt_pos(pos):
    return f"({pos[0]},{pos[1]})"


def print_header(title):
    print("\n" + LINE)
    print(title)
    print(LINE)


def print_paths(model, label):
    """Task 1 console output."""
    p = model.p
    print(f"\nSimulation {label}: {describe(p)}")
    print(f"{'Agent':>5}  {'Start':<8} {'Moves':>5} {'Stayed':>6} {'Visited':>7}"
          f"  Path (first 5 positions)")
    print(f"{'-' * 5}  {'-' * 8} {'-' * 5} {'-' * 6} {'-' * 7}  {'-' * 40}")
    for agent in list(model.agents)[:MAX_TABLE_ROWS]:
        preview = "->".join(fmt_pos(pos) for pos in agent.path[:5])
        if len(agent.path) > 5:
            preview += " ..."
        print(f"{agent.id:>5}  {fmt_pos(agent.path[0]):<8} {agent.moves:>5} "
              f"{agent.stayed:>6} {len(set(agent.path)):>7}  {preview}")
    hidden = len(model.agents) - MAX_TABLE_ROWS
    if hidden > 0:
        print(f"  ... {hidden} more agents (all paths are in TA1_agent_paths.csv)")
    print("  Moves = steps that changed cell, Stayed = steps spent in place,"
          " Visited = distinct cells")


def print_rule_check(model, stats, label):
    """Task 2 console output: shows that each rule behaves as designed."""
    p = model.p
    print(f"\nSimulation {label}: {describe(p)}")
    if p['rule'] == 1:
        rule_text = "picks Up/Down/Left/Right with equal chance (25% each)"
        stay_text = "edge of the grid"
    elif p['rule'] == 2:
        rule_text = "picks randomly among the empty neighbouring cells inside the grid"
        stay_text = "no empty neighbouring cell"
    else:
        rule_text = (f"moves {DIRECTION_NAMES[p['preferred']]} {PREFERRED_PROB:.0%} of the time,"
                     f" other directions {(1 - PREFERRED_PROB) / 3:.1%} each")
        stay_text = "edge of the grid"

    def shares(counts):
        total = sum(counts.values())
        if total == 0:
            return "none"
        text = " | ".join(f"{DIRECTION_NAMES[k]} {100 * counts[k] / total:.1f}%"
                          for k in ('R', 'L', 'U', 'D'))
        return f"{text}  (n = {total})"

    print(f"  Rule              : {rule_text}")
    print(f"  Directions chosen : {shares(stats['chosen'])}")
    print(f"  Moves made        : {shares(stats['directions'])}")
    print(f"  Stayed put        : {stats['total_stayed']} time(s) (blocked by: {stay_text})")
    print(f"  Most agents sharing one cell at any step: {stats['max_stack']}")


def print_final_positions(model, stats, label):
    """Task 3 console output."""
    p = model.p
    width, height = p.grid_size
    print(f"\nSimulation {label}: {describe(p)}")

    # Final positions, six per line
    print("Final positions (agent: x,y):")
    items = [f"{agent.id:>3}:{fmt_pos(agent.position):<8}" for agent in model.agents]
    for i in range(0, len(items), 6):
        print("  " + "  ".join(items[i:i + 6]))

    # Text map of the final distribution (only for grids that fit the console)
    if width <= 30:
        print("Final position map (number = agents in the cell, . = empty,"
              f" top row is y = {height - 1}):")
        for y in range(height - 1, -1, -1):
            row = ""
            for x in range(width):
                count = stats['cell_counts'].get((x, y), 0)
                row += f"{count if count else '.':>3}"
            print(f"  y={y:>2} |{row}")
        print("       +" + "---" * width)
        print("     x =" + "".join(f"{x:>3}" for x in range(width)))

    q = stats['quadrants']
    n = len(stats['finals'])
    cx, cy = stats['centroid']
    print(f"  Centroid (average x, y)          : ({cx:.2f}, {cy:.2f})")
    print(f"  Std. deviation of x, y           : ({stats['std'][0]:.2f}, {stats['std'][1]:.2f})")
    print(f"  Avg distance from the centroid   : {stats['spread']:.2f} cells")
    print(f"  Avg distance from grid center    : {stats['center_dist']:.2f} cells")
    print(f"  Quadrants  Q1 upper-right: {q['Q1']} | Q2 upper-left: {q['Q2']}"
          f" | Q3 lower-left: {q['Q3']} | Q4 lower-right: {q['Q4']}")
    print(f"  Agents on the border cells       : {stats['border']} of {n}"
          f" ({100 * stats['border'] / n:.1f}%)")
    print(f"  Occupied cells at the end        : {stats['occupied']} of {width * height}"
          f" (max {stats['max_cell']} agent(s) in one cell)")
    print(f"  Grid coverage (cells visited)    : {stats['coverage']:.1f}%")
    check = "PASSED - every recorded position is inside the grid" if stats['all_inside'] \
        else "FAILED - an agent left the grid"
    print(f"  Boundary check                   : {check}")


def print_comparison(model_a, stats_a, model_b, stats_b):
    """Task 4 console output."""
    def size(model):
        return f"{model.p.grid_size[0]}x{model.p.grid_size[1]}"

    def rule(model):
        text = RULE_NAMES[model.p.rule]
        if model.p.rule == 3:
            text = f"Preferred ({DIRECTION_NAMES[model.p.preferred]})"
        return text

    rows = [
        ("Number of agents", model_a.p.agents, model_b.p.agents),
        ("Grid size", size(model_a), size(model_b)),
        ("Number of steps", model_a.p.steps, model_b.p.steps),
        ("Movement rule", rule(model_a), rule(model_b)),
        ("Agent density (agents per cell)",
         f"{stats_a['density']:.2f}", f"{stats_b['density']:.2f}"),
        ("Avg distance from start",
         f"{stats_a['displacement']:.2f}", f"{stats_b['displacement']:.2f}"),
        ("Avg moves per agent", f"{stats_a['avg_moves']:.1f}", f"{stats_b['avg_moves']:.1f}"),
        ("Avg steps stayed in place",
         f"{stats_a['avg_stayed']:.1f}", f"{stats_b['avg_stayed']:.1f}"),
        ("Grid coverage", f"{stats_a['coverage']:.1f}%", f"{stats_b['coverage']:.1f}%"),
        ("Avg distance from centroid", f"{stats_a['spread']:.2f}", f"{stats_b['spread']:.2f}"),
        ("Agents on border cells", f"{100 * stats_a['border'] / model_a.p.agents:.1f}%",
         f"{100 * stats_b['border'] / model_b.p.agents:.1f}%"),
        ("Occupied cells at the end", stats_a['occupied'], stats_b['occupied']),
        ("Max agents in one cell (end)", stats_a['max_cell'], stats_b['max_cell']),
    ]
    print(f"{'Metric':<34}{'Simulation A':>20}{'Simulation B':>20}")
    print(f"{'-' * 34}{'-' * 20:>20}{'-' * 20:>20}")
    for name, a, b in rows:
        print(f"{name:<34}{str(a):>20}{str(b):>20}")

    def higher(name, a, b, unit="", decimals=2):
        if abs(a - b) < 1e-9:
            print(f"  {name:<28}: equal ({a:.{decimals}f}{unit})")
        else:
            winner = "A" if a > b else "B"
            print(f"  {name:<28}: Simulation {winner} ({max(a, b):.{decimals}f}{unit}"
                  f" vs {min(a, b):.{decimals}f}{unit})")

    print("\nWhich simulation is higher?")
    higher("Distance from start", stats_a['displacement'], stats_b['displacement'], " cells")
    higher("Grid coverage", stats_a['coverage'], stats_b['coverage'], "%", 1)
    higher("Spread around centroid", stats_a['spread'], stats_b['spread'], " cells")
    higher("Steps stayed in place", stats_a['avg_stayed'], stats_b['avg_stayed'], " per agent", 1)


def save_csv(models):
    """Task 1 and Task 3: record every path and every final position."""
    with open("TA1_agent_paths.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["simulation", "agent", "step", "x", "y"])
        for label, model in models:
            for agent in model.agents:
                for t, (x, y) in enumerate(agent.path):
                    writer.writerow([label, agent.id, t, x, y])
    with open("TA1_final_positions.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["simulation", "agent", "start_x", "start_y",
                         "final_x", "final_y", "moves", "stayed"])
        for label, model in models:
            for agent in model.agents:
                writer.writerow([label, agent.id, agent.path[0][0], agent.path[0][1],
                                 agent.position[0], agent.position[1],
                                 agent.moves, agent.stayed])


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------
def style_grid_axes(ax, width, height):
    """Agents sit in the middle of each cell; grid lines mark cell borders."""
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_aspect('equal')
    step = 1 if width <= 20 else 5
    ax.set_xticks(range(0, width, step))
    ax.set_yticks(range(0, height, step))
    ax.set_xticks([i - 0.5 for i in range(width + 1)], minor=True)
    ax.set_yticks([i - 0.5 for i in range(height + 1)], minor=True)
    ax.grid(True, which='minor', color='lightgray', linewidth=0.6)
    ax.tick_params(which='minor', length=0)
    ax.set_xlabel("x")
    ax.set_ylabel("y")


def agent_color(i, total):
    # Strong colors for small groups, 20 colors (repeating) for bigger groups
    return plt.cm.tab10(i) if total <= 10 else plt.cm.tab20(i % 20)


class PathPanel:
    """Draws one simulation (trails + current positions) on one axes."""

    def __init__(self, ax, model, label):
        self.ax, self.model, self.label = ax, model, label
        width, height = model.p.grid_size
        style_grid_axes(ax, width, height)
        total = len(model.agents)
        self.colors = [agent_color(i, total) for i in range(total)]
        self.paths = [agent.path for agent in model.agents]
        # Small fixed offset per agent so trails that share a grid line stay visible
        self.offsets = [((i % 7) - 3) * 0.05 for i in range(total)]
        starts = [path[0] for path in self.paths]
        ax.scatter([s[0] for s in starts], [s[1] for s in starts], marker='s', s=60,
                   facecolors='none', edgecolors=self.colors, linewidths=1.2, zorder=2)
        self.lines = [ax.plot([], [], '-', color=c, linewidth=1.6, alpha=0.75, zorder=1)[0]
                      for c in self.colors]
        self.dots = ax.scatter([s[0] for s in starts], [s[1] for s in starts], s=140,
                               color=self.colors, edgecolors='black', linewidths=0.6, zorder=3)
        self.title = ax.set_title("")

    def draw(self, frame):
        t = min(frame, self.model.p.steps)          # shorter run stays on its last step
        for line, path, off in zip(self.lines, self.paths, self.offsets):
            line.set_data([pos[0] + off for pos in path[:t + 1]],
                          [pos[1] + off for pos in path[:t + 1]])
        self.dots.set_offsets([path[t] for path in self.paths])
        self.title.set_text(f"Simulation {self.label}: {describe(self.model.p)}\n"
                            f"step {t} of {self.model.p.steps}")
        return self.lines + [self.dots, self.title]


def legend_handles():
    return [Line2D([], [], marker='s', color='gray', markerfacecolor='none', linestyle='',
                   label='Start'),
            Line2D([], [], color='gray', linewidth=1.6, label='Path'),
            Line2D([], [], marker='o', color='gray', markeredgecolor='black', linestyle='',
                   markersize=9, label='Current position')]


def draw_heatmap(ax, values, width, height, title, cmap, annotate):
    image = ax.imshow(values, origin='lower', cmap=cmap, aspect='equal', vmin=0,
                      extent=(-0.5, width - 0.5, -0.5, height - 0.5))
    style_grid_axes(ax, width, height)
    ax.set_title(title, fontsize=10)
    colorbar = plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.locator = MaxNLocator(integer=True)     # counts are whole numbers
    colorbar.update_ticks()
    if annotate and width <= 15:
        top = max(max(row) for row in values)
        for y in range(height):
            for x in range(width):
                if values[y][x]:
                    color = 'white' if values[y][x] > top / 2 else 'black'
                    ax.text(x, y, str(values[y][x]), ha='center', va='center',
                            fontsize=8, color=color)


def analysis_figure(models):
    """Task 3 figure: final positions and how often each cell was visited."""
    fig, axes = plt.subplots(len(models), 2, figsize=(11, 5 * len(models)))
    for row, (label, model) in enumerate(models):
        width, height = model.p.grid_size
        finals = [[0] * width for _ in range(height)]
        visits = [[0] * width for _ in range(height)]
        for agent in model.agents:
            finals[agent.position[1]][agent.position[0]] += 1
            for x, y in agent.path:
                visits[y][x] += 1
        draw_heatmap(axes[row][0], finals, width, height,
                     f"Simulation {label}: final positions (agents per cell)", 'Blues', True)
        half_x, half_y = math.ceil(width / 2), math.ceil(height / 2)
        axes[row][0].axvline(half_x - 0.5, color='red', linestyle='--', linewidth=1)
        axes[row][0].axhline(half_y - 0.5, color='red', linestyle='--', linewidth=1)
        draw_heatmap(axes[row][1], visits, width, height,
                     f"Simulation {label}: visits per cell over the whole run", 'YlOrRd', False)
    fig.suptitle("Final Position Distribution (red dashed lines = quadrant borders)")
    fig.tight_layout()
    return fig


def spread_figure(models):
    """Task 4 figure: how the agents spread out step by step."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    for label, model in models:
        steps = range(len(model.displacement_history))
        ax1.plot(steps, model.displacement_history, label=f"{label}: {describe(model.p)}")
        ax2.plot(steps, model.coverage_history, label=f"{label}: {describe(model.p)}")
    ax1.set_title("Average distance from starting cell")
    ax1.set_xlabel("Step")
    ax1.set_ylabel("Distance (cells)")
    ax2.set_title("Grid coverage (cells visited at least once)")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Coverage (%)")
    ax2.set_ylim(0, 105)
    for ax in (ax1, ax2):
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='lower right')
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------
def main():
    print(LINE)
    print("RANDOM WALK SIMULATION USING AGENTPY - MODIFIED CODE (TA1)")
    print(LINE)

    # -------- INPUT --------
    print("[INPUT] Enter the parameters of the two simulations to compare.")
    seed = ask_seed()
    params_a = get_scenario("A", seed)
    params_b = get_scenario("B", seed)

    # -------- PROCESS --------
    print_header("[PROCESS] Running the simulations")
    models = []
    for params in (params_a, params_b):
        model = RandomWalkModel(params)
        model.run(display=False)          # AgentPy runs setup, then step() 'steps' times
        print(f"Simulation {params['label']}: {describe(params)} -> {model.t} steps completed")
        models.append((params['label'], model))
    print(f"Seed used for both simulations: {seed}")
    print("(Same seed = same starting cells when the agent count and grid size match.)")
    (_, model_a), (_, model_b) = models
    stats_a, stats_b = analyze(model_a), analyze(model_b)

    # -------- OUTPUT --------
    print_header("[OUTPUT] TASK 1 - AGENT PATHS")
    print_paths(model_a, "A")
    print_paths(model_b, "B")

    print_header("[OUTPUT] TASK 2 - MOVEMENT RULE CHECK")
    print_rule_check(model_a, stats_a, "A")
    print_rule_check(model_b, stats_b, "B")

    print_header("[OUTPUT] TASK 3 - FINAL POSITIONS AND DISTRIBUTION")
    print_final_positions(model_a, stats_a, "A")
    print_final_positions(model_b, stats_b, "B")

    print_header("[OUTPUT] TASK 4 - SCENARIO COMPARISON")
    print_comparison(model_a, stats_a, model_b, stats_b)

    # -------- Save records and figures --------
    save_csv(models)

    # Figure 1: path animation (A and B side by side)
    fig1, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    panels = [PathPanel(ax, model, label) for ax, (label, model) in zip(axes, models)]
    fig1.legend(handles=legend_handles(), loc='lower center', ncol=3)
    last_frame = max(model_a.p.steps, model_b.p.steps)
    for panel in panels:
        panel.draw(last_frame)
    fig1.tight_layout(rect=(0, 0.06, 1, 1))
    # The final frame shows the complete path of every agent
    fig1.savefig("TA1_fig1_agent_paths.png", dpi=150, bbox_inches='tight')

    fig2 = analysis_figure(models)
    fig2.savefig("TA1_fig2_final_positions.png", dpi=150, bbox_inches='tight')
    fig3 = spread_figure(models)
    fig3.savefig("TA1_fig3_spread_over_time.png", dpi=150, bbox_inches='tight')

    print_header("[OUTPUT] FILES SAVED")
    print("  TA1_agent_paths.csv            - every position of every agent, step by step")
    print("  TA1_final_positions.csv        - start and final position of every agent")
    print("  TA1_fig1_agent_paths.png       - complete paths of all agents (Task 1)")
    print("  TA1_fig2_final_positions.png   - final position distribution (Task 3)")
    print("  TA1_fig3_spread_over_time.png  - spread of the agents over time (Task 4)")

    # -------- Interactive Animation --------
    def update(frame):
        artists = []
        for panel in panels:
            artists += panel.draw(frame)
        return artists

    print("\nShowing the animation and charts. Close all figure windows to end the program.")
    ani = animation.FuncAnimation(fig1, update, frames=last_frame + 1, interval=250,
                                  init_func=lambda: update(0), blit=False, repeat=False)
    plt.show()
    print("Program finished.")
    return ani


if __name__ == "__main__":
    main()
