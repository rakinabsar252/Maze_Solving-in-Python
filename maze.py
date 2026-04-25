import random

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[0] * cols for _ in range(rows)]  # 0=open, 1=wall
        self.start = (1, 1)
        self.end = (rows - 2, cols - 2)

    def generate(self):
        """Recursive backtracking maze generation."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c] = 1  # fill all walls

        def carve(r, c):
            self.grid[r][c] = 0
            dirs = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            random.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 < nr < self.rows - 1 and 0 < nc < self.cols - 1 and self.grid[nr][nc] == 1:
                    self.grid[r + dr // 2][c + dc // 2] = 0
                    carve(nr, nc)

        carve(1, 1)
        self.grid[self.start[0]][self.start[1]] = 0
        self.grid[self.end[0]][self.end[1]] = 0

    def clear(self):
        """Clear all walls."""
        self.grid = [[0] * self.cols for _ in range(self.rows)]

    def is_valid(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == 0

    def neighbors(self, r, c):
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if self.is_valid(nr, nc):
                yield nr, nc

    def set_cell(self, r, c, val):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.grid[r][c] = val
