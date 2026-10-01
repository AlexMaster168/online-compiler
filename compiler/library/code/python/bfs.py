# Поиск в ширину: очередь, O(V + E). Расстояние — число рёбер от старта.
from collections import deque

graph = {0: [1, 2], 1: [0, 3], 2: [0, 4], 3: [1, 5], 4: [2, 5], 5: [3, 4]}


def bfs(start):
    dist = {start: 0}
    order = []
    queue = deque([start])
    while queue:
        v = queue.popleft()
        order.append(v)
        for u in graph[v]:
            if u not in dist:
                dist[u] = dist[v] + 1
                queue.append(u)
    return order, dist


order, dist = bfs(0)
print("BFS order:", *order)
print("Distances:", *(dist[v] for v in sorted(graph)))
