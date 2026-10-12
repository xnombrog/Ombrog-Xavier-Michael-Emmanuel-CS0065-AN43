# Technical Assessment 1 - Random Walk Simulation

This folder contains the implementation and supporting files for Technical Assessment 1 (TA1) for CS0065 - AN43.

## Project overview

The project is a Python-based random walk simulation built with AgentPy and Matplotlib. It models multiple agents moving on a grid under different movement rules and compares two simulation scenarios (A and B).

The program covers the four required tasks:

- Task 1: track and visualize each agent's path
- Task 2: compare movement rules (random walk, avoid each other, preferred direction)
- Task 3: analyze final positions and spatial distribution
- Task 4: compare two scenarios side by side

## Files in this folder

- `TA1_random_walk.py` — main simulation script
- `TA1_Ombrog.pdf` — submitted assessment/report document
- `TA1_agent_paths.csv` — generated path data for all agents
- `TA1_final_positions.csv` — generated final position summary
- `TA1_fig1_agent_paths.png` — chart showing the overall paths of the agents
- `TA1_fig2_final_positions.png` — heatmap of final position distribution
- `TA1_fig3_spread_over_time.png` — comparison of spread and coverage over time

## Requirements

Install the required Python libraries before running the simulation:

```bash
pip install agentpy matplotlib
```

## How to run

From this folder, execute:

```bash
python TA1_random_walk.py
```

When the script runs, it will prompt you to enter parameters for two simulations, including:

- number of agents
- grid size
- number of steps
- movement rule
- preferred direction (for the biased rule)
- optional random seed

The program then:

1. runs both simulations,
2. prints the analysis results in the console,
3. saves CSV summaries,
4. generates the required figures,
5. displays the animation and charts.

## Output description

The script exports several result files:

- `TA1_agent_paths.csv`: every agent's position history across the simulation
- `TA1_final_positions.csv`: start and final positions for each agent
- `TA1_fig1_agent_paths.png`: agent trails and current positions
- `TA1_fig2_final_positions.png`: final distribution heatmap
- `TA1_fig3_spread_over_time.png`: spread/coverage comparison across time

## Author

OMBROG, Xavier Michael Emmanuel, N.

## Course section

CS0065 - AN43
