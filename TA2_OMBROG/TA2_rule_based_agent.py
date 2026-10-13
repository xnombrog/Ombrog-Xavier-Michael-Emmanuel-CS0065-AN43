"""
CS0065 - Intelligent Systems
Technical Assessment 2: Rule-Based Agent (Vacuum Cleaner)

Task 1 - Set up the environment: the rooms are stored in a dictionary, the user
         sets the initial state of each room, and two helper functions check
         whether a room is dirty and clean a room.
Task 2 - Rule-based agent: the VacuumAgent class has a perceive_and_act()
         method that follows two rules and a move() method that switches rooms.
           Rule 1: If the current room is dirty, clean it.
           Rule 2: If the current room is clean, move to the other room.
Task 3 - Simulation: the user enters the number of steps, and after every step
         the program prints the agent's location, the action taken and the
         current state of the environment.
Bonus  - Three rooms (A, B, C): the agent randomly chooses which dirty room to
         clean next, stays idle once every room is clean, and its movement is
         shown on a text-based grid.
"""

import random

CLEAN = "Clean"
DIRTY = "Dirty"


# ===========================================================================
# TASK 1: SET UP THE ENVIRONMENT
# ===========================================================================
def ask_room_state(room):
    """Ask the user whether a room starts Dirty or Clean (re-asks on bad input)."""
    while True:
        answer = input(f"Is room {room} Dirty or Clean? ").strip().lower()
        if answer in ("dirty", "d"):
            return DIRTY
        if answer in ("clean", "c"):
            return CLEAN
        print("   Invalid input. Please type Dirty or Clean.")


def create_environment(rooms):
    """Build the environment dictionary, e.g. {'A': 'Dirty', 'B': 'Clean'}."""
    environment = {}
    for room in rooms:
        environment[room] = ask_room_state(room)
    return environment


def is_dirty(environment, room):
    """Return True if the given room is dirty."""
    return environment[room] == DIRTY


def clean_room(environment, room):
    """Clean the given room by updating its state in the environment."""
    environment[room] = CLEAN


def ask_steps():
    """Ask how many steps the simulation should run (must be 1 or more)."""
    while True:
        answer = input("How many steps should the agent run? ").strip()
        try:
            steps = int(answer)
        except ValueError:
            steps = 0
        if steps > 0:
            return steps
        print("   Invalid input. Please enter a whole number greater than 0.")


# ===========================================================================
# TASK 2: IMPLEMENT THE RULE-BASED AGENT
# ===========================================================================
class VacuumAgent:
    """Simple rule-based vacuum cleaner for two rooms (A and B)."""

    def __init__(self, start_room="A"):
        self.location = start_room      # the room the agent is currently in

    def move(self):
        """Switch to the other room (A -> B or B -> A)."""
        if self.location == "A":
            self.location = "B"
        else:
            self.location = "A"

    def perceive_and_act(self, environment):
        """Perceive the current room, apply the rules, and return the action taken."""
        if is_dirty(environment, self.location):
            # Rule 1: If the current room is dirty, clean it.
            clean_room(environment, self.location)
            return "cleaned", f"Room {self.location} has been cleaned."
        # Rule 2: If the current room is clean, move to the other room.
        self.move()
        return "moved", f"Moving to room {self.location}"


# ===========================================================================
# TASK 3: RUN THE SIMULATION (TWO ROOMS)
# ===========================================================================
def run_two_room_simulation():
    # INPUT: initial state of each room and number of steps
    environment = create_environment(["A", "B"])
    print()
    steps = ask_steps()

    # PROCESS: the agent starts in room A and applies its rules once per step
    agent = VacuumAgent(start_room="A")
    counts = {"cleaned": 0, "moved": 0}
    for step in range(1, steps + 1):
        print()
        print(f"Step {step}: Agent is in room {agent.location}")
        action, message = agent.perceive_and_act(environment)
        counts[action] += 1

        # OUTPUT after each step: action taken and current state of the environment
        print(message)
        print(f"Environment state: {environment}")

    # OUTPUT: summary of the whole run
    print()
    print(f"Simulation finished after {steps} step(s): "
          f"{counts['cleaned']} clean action(s), {counts['moved']} move(s).")
    print(f"Final location: room {agent.location} | Final state: {environment}")


# ===========================================================================
# BONUS TASK: THREE ROOMS, RANDOM CHOICE OF DIRTY ROOM, TEXT-BASED GRID
# ===========================================================================
class MultiRoomVacuumAgent(VacuumAgent):
    """Rule-based vacuum cleaner that works with any number of rooms."""

    def move_to(self, room):
        """Move directly to the chosen room."""
        self.location = room

    def perceive_and_act(self, environment):
        """Apply the updated rules for three (or more) rooms."""
        if is_dirty(environment, self.location):
            # Rule 1: If the current room is dirty, clean it.
            clean_room(environment, self.location)
            return "cleaned", f"Room {self.location} has been cleaned."

        dirty_rooms = [room for room in environment if is_dirty(environment, room)]
        if dirty_rooms:
            # Rule 2: If the current room is clean, move to a randomly chosen dirty room.
            self.move_to(random.choice(dirty_rooms))
            return "moved", f"Moving to room {self.location}"

        # Rule 3: If every room is clean, stay where you are.
        return "idle", "All rooms are clean. Agent is idle."


def show_grid(environment, agent_location):
    """Text-based grid: the agent's room shows 'Agent', other rooms show their state."""
    cells = []
    for room in environment:
        label = "Agent" if room == agent_location else environment[room]
        cells.append(f"[{room}-{label}]")
    print("  ".join(cells))


def run_three_room_simulation():
    # INPUT: initial state of rooms A, B and C and number of steps
    environment = create_environment(["A", "B", "C"])
    print()
    steps = ask_steps()

    # PROCESS: the agent starts in room A and applies its rules once per step
    agent = MultiRoomVacuumAgent(start_room="A")
    counts = {"cleaned": 0, "moved": 0, "idle": 0}
    for step in range(1, steps + 1):
        print()
        print(f"Step {step}:")
        show_grid(environment, agent.location)          # before the action
        action, message = agent.perceive_and_act(environment)
        counts[action] += 1

        # OUTPUT after each step: action taken and the updated grid
        print(message)
        show_grid(environment, agent.location)          # after the action

    # OUTPUT: summary of the whole run
    print()
    print(f"Simulation finished after {steps} step(s): "
          f"{counts['cleaned']} clean action(s), {counts['moved']} move(s), "
          f"{counts['idle']} idle step(s).")
    print(f"Final location: room {agent.location} | Final state: {environment}")


# ===========================================================================
# MAIN PROGRAM
# ===========================================================================
def main():
    print("=" * 55)
    print("RULE-BASED AGENT: VACUUM CLEANER SIMULATION")
    print("=" * 55)
    while True:
        print("[1] Two rooms: A and B (Tasks 1-3)")
        print("[2] Three rooms: A, B and C with text-based grid (Bonus Task)")
        print("[3] Exit")
        choice = input("Choose an option (1-3): ").strip()
        print()
        if choice == "1":
            run_two_room_simulation()
        elif choice == "2":
            run_three_room_simulation()
        elif choice == "3":
            print("Program ended.")
            break
        else:
            print("   Invalid choice. Please enter 1, 2 or 3.")
            continue
        print("\n" + "-" * 55)


if __name__ == "__main__":
    main()
