# Maze_Solving-in-Python
# Maze Solver

A visual maze solver built with Python and Tkinter.

## Features
- Procedural maze generation (recursive backtracking)
- Three solving algorithms: BFS, DFS, A*
- Step-by-step animated visualization
- Interactive drawing (walls, start, end)
- Multiple maze sizes (15×15 to 41×41)
- Speed control (Slow → Instant)
- Live stats: visited cells, path length

## Run
```bash
python main.py
```
No dependencies beyond Python 3.8+ standard library.

## Files
| File | Purpose |
|---|---|
| `main.py` | Entry point |
| `ui.py` | Tkinter GUI, animation loop |
| `maze.py` | Maze grid, generation, neighbor logic |
| `algorithms.py` | BFS, DFS, A* implementations |

## Controls
- **Generate Maze** — random maze via recursive backtracking
- **Draw Mode** — Wall / Erase / Start / End (click or drag on canvas)
- **Algorithm** — BFS (shortest), DFS (exploratory), A* (optimal+fast)
- **Speed** — Slow / Normal / Fast / Instant
- **Run** — animate the solve
- **Stop / Reset** — pause or clear the search
