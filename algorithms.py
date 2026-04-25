from collections import deque
import heapq

def bfs(maze, start, end):
    """Breadth-First Search — guarantees shortest path."""
    queue = deque([start])
    visited = {start: None}
    order = []

    while queue:
        cur = queue.popleft()
        order.append(cur)
        if cur == end:
            return _reconstruct(visited, start, end), order

        for nb in maze.neighbors(*cur):
            if nb not in visited:
                visited[nb] = cur
                queue.append(nb)

    return None, order  # no path


def dfs(maze, start, end):
    """Depth-First Search — explores deep, not optimal."""
    stack = [start]
    visited = {start: None}
    order = []

    while stack:
        cur = stack.pop()
        if cur in order:
            continue
        order.append(cur)
        if cur == end:
            return _reconstruct(visited, start, end), order

        for nb in maze.neighbors(*cur):
            if nb not in visited:
                visited[nb] = cur
                stack.append(nb)

    return None, order


def astar(maze, start, end):
    """A* Search — heuristic-guided, optimal and efficient."""
    def h(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    g = {start: 0}
    f = {start: h(start, end)}
    parent = {start: None}
    open_set = [(f[start], start)]
    closed = set()
    order = []

    while open_set:
        _, cur = heapq.heappop(open_set)
        if cur in closed:
            continue
        closed.add(cur)
        order.append(cur)

        if cur == end:
            return _reconstruct(parent, start, end), order

        for nb in maze.neighbors(*cur):
            if nb in closed:
                continue
            ng = g[cur] + 1
            if ng < g.get(nb, float('inf')):
                g[nb] = ng
                f[nb] = ng + h(nb, end)
                parent[nb] = cur
                heapq.heappush(open_set, (f[nb], nb))

    return None, order


def _reconstruct(parent, start, end):
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    return path if path[0] == start else None
