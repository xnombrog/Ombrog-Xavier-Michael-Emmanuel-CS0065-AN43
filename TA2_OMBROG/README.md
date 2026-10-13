# Technical Assessment 2 - Rule-Based Vacuum Cleaner Agent

This folder contains the implementation and supporting files for Technical Assessment 2 (TA2) for CS0065 - AN43.

## Project overview

The project implements a simple rule-based intelligent agent that acts as a vacuum cleaner. The agent perceives the state of each room, applies rules to decide its next move, and continues the simulation for a user-specified number of steps.

The program includes:

- a two-room simulation for the main tasks
- a three-room bonus version with a text-based grid
- room cleaning logic
- user-driven initial room states

## Files in this folder

- `TA2_rule_based_agent.py` — main Python program
- `TA2_OMBROG.pdf` — submitted assessment/report document

## How to run

From this folder, execute:

```bash
python TA2_rule_based_agent.py
```

The program will display a menu with the following options:

1. Two rooms: A and B
2. Three rooms: A, B and C (bonus)
3. Exit

## Main logic

### Two-room version

The agent follows these rules:

- If the current room is dirty, clean it.
- If the current room is clean, move to the other room.

The user is prompted to enter the initial state of each room as either Dirty or Clean, then the simulation runs for the chosen number of steps.

### Three-room bonus version

The extended program adds:

- random selection of a dirty room to visit next
- an idle state when all rooms are clean
- a text-based room grid showing the agent location and room states

## Example workflow

1. Run the script.
2. Choose option 1 or 2.
3. Enter the state of each room.
4. Enter the number of steps.
5. Review the step-by-step simulation output.

## Author

OMBROG, Xavier Michael Emmanuel, N.

## Course section

CS0065 - AN43
