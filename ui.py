import tkinter as tk
from tkinter import ttk, messagebox
from maze import Maze                          # Custom Maze class for grid logic
from algorithms import bfs, dfs, astar        # Pathfinding algorithm implementations

# ── Color palette (Catppuccin-inspired dark theme) ────────────────────────────
COLORS = {
    "bg":       "#1E1E2E",   # Main window background
    "panel":    "#2A2A3E",   # Left control panel background
    "wall":     "#CDD6F4",   # Wall cell color
    "open":     "#181825",   # Empty/open cell color
    "start":    "#A6E3A1",   # Start cell (green)
    "end":      "#F38BA8",   # End cell (red/pink)
    "visited":  "#74C7EC",   # Cells visited during search (blue)
    "frontier": "#FAB387",   # Frontier/queue cells (orange)
    "path":     "#EC0707",   # Final solution path (bright red)
    "grid":     "#313244",   # Grid line / button hover color
    "text":     "#CDD6F4",   # General text color
    "accent":   "#89B4FA",   # Accent color for headings and highlights
    "btn_bg":   "#313244",   # Default button background
    "btn_fg":   "#CDD6F4",   # Default button foreground (text)
}

# ── Map display names to algorithm functions and speed labels to delays (ms) ──
ALGO_MAP = {"BFS (Shortest)": bfs, "DFS (Explore)": dfs, "A* (Smart)": astar}
SPEEDS   = {"Slow": 100, "Normal": 20, "Fast": 5, "Instant": 0}


class MazeSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maze Solver")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(False, False)   # Prevent window resizing

        # ── Default maze dimensions and cell pixel size ────────────────────
        self.rows = 21
        self.cols = 21
        self.cell = 22                       # Each cell is 22×22 pixels

        # ── Core state variables ───────────────────────────────────────────
        self.maze      = Maze(self.rows, self.cols)
        self.draw_mode = tk.StringVar(value="Wall")           # Active drawing tool
        self.algo_var  = tk.StringVar(value="BFS (Shortest)") # Selected algorithm
        self.speed_var = tk.StringVar(value="Normal")         # Animation speed
        self.running   = False        # True while animation is in progress
        self._after_id = None         # ID of the pending `after` callback (for cancellation)

        # ── Animation state ────────────────────────────────────────────────
        self._anim_steps    = []      # List of (kind, cell) steps to animate
        self._anim_idx      = 0       # Index of the current animation step
        self._visited_count = 0       # Running count of visited cells
        self._path_cells    = []      # Cells on the final solution path

        self._build_ui()              # Construct all UI widgets
        self._generate_maze()         # Generate an initial maze on startup

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Left control panel ─────────────────────────────────────────────
        left = tk.Frame(self.root, bg=COLORS["panel"], padx=12, pady=12)
        left.pack(side="left", fill="y")

        # Maze size presets
        self._section(left, "MAZE")
        for size_label, (r, c) in [("Small 15×15", (15,15)), ("Medium 21×21",(21,21)),
                                    ("Large 31×31",(31,31)), ("Huge 41×41",(41,41))]:
            self._btn(left, size_label, lambda r=r,c=c: self._resize(r,c))

        self._btn(left, "Generate Maze", self._generate_maze, accent=True)
        self._btn(left, "Clear Walls",   self._clear_maze)

        # Draw mode radio buttons (Wall / Erase / Start / End)
        self._section(left, "DRAW MODE")
        for m in ["Wall", "Erase", "Start", "End"]:
            tk.Radiobutton(left, text=m, variable=self.draw_mode, value=m,
                           bg=COLORS["panel"], fg=COLORS["text"],
                           selectcolor=COLORS["btn_bg"], activebackground=COLORS["panel"],
                           activeforeground=COLORS["accent"], font=("Courier", 10)).pack(anchor="w")

        # Algorithm selection radio buttons
        self._section(left, "ALGORITHM")
        for a in ALGO_MAP:
            tk.Radiobutton(left, text=a, variable=self.algo_var, value=a,
                           bg=COLORS["panel"], fg=COLORS["text"],
                           selectcolor=COLORS["btn_bg"], activebackground=COLORS["panel"],
                           activeforeground=COLORS["accent"], font=("Courier", 10)).pack(anchor="w")

        # Speed dropdown (Slow / Normal / Fast / Instant)
        self._section(left, "SPEED")
        speed_cb = ttk.Combobox(left, textvariable=self.speed_var,
                                values=list(SPEEDS.keys()), state="readonly", width=12)
        speed_cb.pack(anchor="w", pady=(2,8))

        # Control buttons: Run, Stop, Reset
        self._btn(left, "▶  Run",   self._run_solver, accent=True)
        self._btn(left, "⏹  Stop",  self._stop)
        self._btn(left, "↺  Reset", self._reset_search)

        # Live statistics display
        self._section(left, "STATS")
        self.lbl_algo    = self._stat_label(left, "Algorithm", "—")   # Current algorithm name
        self.lbl_visited = self._stat_label(left, "Visited",   "0")   # Cells visited so far
        self.lbl_path    = self._stat_label(left, "Path len",  "—")   # Final path length

        # Color legend explaining each cell state
        self._section(left, "LEGEND")
        for label, key in [("Start","start"),("End","end"),("Wall","wall"),
                            ("Visited","visited"),("Frontier","frontier"),("Path","path")]:
            row = tk.Frame(left, bg=COLORS["panel"])
            row.pack(anchor="w", pady=1)
            tk.Label(row, width=2, bg=COLORS[key]).pack(side="left", padx=(0,6))  # Color swatch
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"],
                     font=("Courier", 9)).pack(side="left")

        # ── Right side: canvas area ────────────────────────────────────────
        right = tk.Frame(self.root, bg=COLORS["bg"], padx=8, pady=8)
        right.pack(side="left")

        # The main drawing canvas sized to fit the current grid
        w = self.cols * self.cell
        h = self.rows * self.cell
        self.canvas = tk.Canvas(right, width=w, height=h,
                                bg=COLORS["bg"], highlightthickness=0, cursor="crosshair")
        self.canvas.pack()

        # Mouse event bindings for interactive drawing
        self.canvas.bind("<Button-1>",        self._on_click)   # Single click
        self.canvas.bind("<B1-Motion>",       self._on_drag)    # Click-and-drag
        self.canvas.bind("<ButtonRelease-1>", lambda e: None)   # Release (no-op)

        # Status bar at the bottom of the canvas
        self.status_var = tk.StringVar(value="Generate a maze or draw your own, then click Run.")
        tk.Label(right, textvariable=self.status_var, bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Courier", 10), anchor="w").pack(fill="x")

    def _section(self, parent, text):
        """Render a bold section header label in the control panel."""
        tk.Label(parent, text=text, bg=COLORS["panel"], fg=COLORS["accent"],
                 font=("Courier", 10, "bold")).pack(anchor="w", pady=(10,2))

    def _btn(self, parent, text, cmd, accent=False):
        """
        Create a flat-style button.
        accent=True renders it with the blue accent color (used for primary actions).
        """
        fg = COLORS["bg"] if accent else COLORS["btn_fg"]
        bg = COLORS["accent"] if accent else COLORS["btn_bg"]
        tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                  activebackground=COLORS["grid"], activeforeground=COLORS["text"],
                  font=("Courier", 10), relief="flat", padx=8, pady=3,
                  cursor="hand2").pack(fill="x", pady=2)

    def _stat_label(self, parent, label, val):
        """
        Create a two-column stat row: 'Label:  Value'.
        Returns the value Label widget so it can be updated later.
        """
        f = tk.Frame(parent, bg=COLORS["panel"])
        f.pack(anchor="w", fill="x")
        tk.Label(f, text=f"{label}:", bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Courier", 9), width=10, anchor="w").pack(side="left")
        lbl = tk.Label(f, text=val, bg=COLORS["panel"], fg=COLORS["accent"],
                       font=("Courier", 9, "bold"))
        lbl.pack(side="left")
        return lbl   # Caller stores this reference to update the value dynamically

    # ── Maze Management ────────────────────────────────────────────────────────
    def _resize(self, rows, cols):
        """Resize the grid and canvas, then regenerate a maze at the new dimensions."""
        self._stop()
        self.rows, self.cols = rows, cols
        self.maze = Maze(rows, cols)
        w, h = cols * self.cell, rows * self.cell
        self.canvas.config(width=w, height=h)
        self._generate_maze()

    def _generate_maze(self):
        """Create a fresh maze using the Maze generator and redraw everything."""
        self._stop()
        self.maze = Maze(self.rows, self.cols)
        self.maze.generate()          # Runs the internal maze-generation algorithm
        self._reset_display()
        self._draw_all()
        self.status_var.set("Maze ready. Choose algorithm and click Run.")

    def _clear_maze(self):
        """Remove all walls, leaving a fully open grid for manual drawing."""
        self._stop()
        self.maze.clear()
        self._reset_display()
        self._draw_all()
        self.status_var.set("Canvas cleared. Draw walls or generate a maze.")

    def _reset_search(self):
        """Clear only the search overlay (visited/path colors) without touching walls."""
        self._stop()
        self._reset_display()
        self._draw_all()
        self.status_var.set("Reset. Ready to run again.")

    def _reset_display(self):
        """
        Reset all search-related state:
        - Clears per-cell visited/path state dictionary
        - Resets counters and stat labels to defaults
        """
        self._visited_states = {}    # Maps (r,c) -> "visited" | "path"
        self._path_cells     = []
        self._visited_count  = 0
        self.lbl_visited.config(text="0")
        self.lbl_path.config(text="—")
        self.lbl_algo.config(text="—")

    # ── Canvas Rendering ───────────────────────────────────────────────────────
    def _draw_all(self):
        """Redraw every cell in the grid from scratch."""
        self.canvas.delete("all")    # Wipe the entire canvas
        for r in range(self.rows):
            for c in range(self.cols):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c, color=None):
        """
        Draw (or redraw) a single cell at grid position (r, c).
        Color priority (if not explicitly provided):
          1. Start cell
          2. End cell
          3. Wall
          4. Visited/path state from _visited_states
          5. Default open color
        Each cell is tagged 'c_r_c' so it can be individually replaced.
        """
        cl = self.cell
        x, y = c * cl, r * cl           # Pixel top-left corner of this cell

        if color is None:
            if (r, c) == self.maze.start:
                color = COLORS["start"]
            elif (r, c) == self.maze.end:
                color = COLORS["end"]
            elif self.maze.grid[r][c] == 1:
                color = COLORS["wall"]
            else:
                # Look up any search-state color, defaulting to "open"
                st = self._visited_states.get((r, c), "open")
                color = COLORS.get(st, COLORS["open"])

        tag = f"c_{r}_{c}"
        self.canvas.delete(tag)          # Remove previous version of this cell
        # Draw a filled rectangle with a 1-pixel gap from the cell boundary (grid gap effect)
        self.canvas.create_rectangle(x+1, y+1, x+cl-1, y+cl-1,
                                     fill=color, outline="", tags=tag)

    # ── Mouse Interaction ──────────────────────────────────────────────────────
    def _cell_from_event(self, event):
        """Convert a mouse pixel coordinate to a (row, col) grid position.
        Returns None if the click is outside the grid bounds."""
        c = event.x // self.cell
        r = event.y // self.cell
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None

    def _on_click(self, event):
        """Handle a single left-click on the canvas (ignored while solver runs)."""
        if self.running: return
        pos = self._cell_from_event(event)
        if pos:
            self._apply_draw(pos)

    def _on_drag(self, event):
        """Handle click-and-drag painting across multiple cells."""
        if self.running: return
        pos = self._cell_from_event(event)
        if pos:
            self._apply_draw(pos)

    def _apply_draw(self, pos):
        """
        Modify the maze grid at (r, c) according to the active draw mode:
        - Wall:  set cell to 1 (blocked)
        - Erase: set cell to 0 (open)
        - Start: move the start marker here and open the cell
        - End:   move the end marker here and open the cell
        Then immediately redraw that single cell.
        """
        r, c = pos
        mode = self.draw_mode.get()
        if mode == "Wall":
            self.maze.grid[r][c] = 1
        elif mode == "Erase":
            self.maze.grid[r][c] = 0
        elif mode == "Start":
            self.maze.start = (r, c)
            self.maze.grid[r][c] = 0    # Ensure the start cell is passable
        elif mode == "End":
            self.maze.end = (r, c)
            self.maze.grid[r][c] = 0    # Ensure the end cell is passable
        self._draw_cell(r, c)

    # ── Solver & Animation ─────────────────────────────────────────────────────
    def _run_solver(self):
        """
        Entry point for the Run button.
        1. Resets any previous search display.
        2. Calls the selected algorithm to get (path, visit_order).
        3. Converts the result into a flat list of animation steps.
        4. Starts playback at the chosen speed.
        """
        if self.running: return          # Ignore if already animating

        self._reset_display()
        self._draw_all()

        algo_name = self.algo_var.get()
        algo_fn   = ALGO_MAP[algo_name]
        self.lbl_algo.config(text=algo_name.split()[0])   # Show just "BFS", "DFS", or "A*"

        # Run the algorithm synchronously to get all steps at once
        path, order = algo_fn(self.maze, self.maze.start, self.maze.end)

        # Build animation step list: first all visited cells, then the path
        self._anim_steps = []
        for cell in order:
            if cell not in (self.maze.start, self.maze.end):
                self._anim_steps.append(("visited", cell))   # Mark as explored
        if path:
            for cell in path:
                if cell not in (self.maze.start, self.maze.end):
                    self._anim_steps.append(("path", cell))  # Highlight solution
        else:
            self._anim_steps.append(("no_path", None))       # Signal no solution found

        # Initialize animation pointers and counters
        self._anim_idx      = 0
        self._path_cells    = path or []
        self._visited_count = 0
        self.running        = True

        delay = SPEEDS[self.speed_var.get()]
        if delay == 0:
            self._instant_play()         # Render everything in one shot
        else:
            self._step_play(delay)       # Animate step by step with delays

    def _instant_play(self):
        """Apply all animation steps immediately (no delay) for 'Instant' speed."""
        for kind, cell in self._anim_steps:
            self._apply_step(kind, cell)
        self.running = False
        self._finish()

    def _step_play(self, delay):
        """
        Recursive timer-based animation: apply one step, then schedule the next.
        Stops automatically when all steps are consumed or self.running is False.
        """
        if not self.running or self._anim_idx >= len(self._anim_steps):
            self.running = False
            self._finish()
            return
        kind, cell = self._anim_steps[self._anim_idx]
        self._apply_step(kind, cell)
        self._anim_idx += 1
        # Schedule the next frame; store ID so it can be cancelled by _stop()
        self._after_id = self.root.after(delay, lambda: self._step_play(delay))

    def _apply_step(self, kind, cell):
        """
        Render a single animation step:
        - 'visited': color the cell blue and increment the visited counter
        - 'path':    color the cell red (solution path)
        - 'no_path': (handled implicitly via _finish with empty path)
        """
        if kind == "visited" and cell:
            self._visited_states[cell] = "visited"
            self._visited_count += 1
            self.lbl_visited.config(text=str(self._visited_count))
            self._draw_cell(*cell, color=COLORS["visited"])
        elif kind == "path" and cell:
            self._visited_states[cell] = "path"
            self._draw_cell(*cell, color=COLORS["path"])

    def _finish(self):
        """
        Called when animation completes.
        Updates the status bar and path-length stat.
        Start and end cells are excluded from the displayed path length.
        """
        # Subtract 2 to exclude the start and end nodes from the count
        path_len = len(self._path_cells) - 2 if len(self._path_cells) > 2 else 0
        if self._path_cells:
            self.lbl_path.config(text=str(path_len))
            self.status_var.set(f"Done! Visited {self._visited_count} cells · Path length {path_len}")
        else:
            self.lbl_path.config(text="✗")
            self.status_var.set("No path found between start and end.")

    def _stop(self):
        """
        Halt any running animation:
        - Sets self.running = False so the step loop exits
        - Cancels the pending `after` callback to prevent ghost frames
        """
        self.running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None


# ── Entry Point ────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = MazeSolverApp(root)
    root.mainloop()    # Start the Tkinter event loop

if __name__ == "__main__":
    main()