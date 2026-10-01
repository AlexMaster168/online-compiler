# Дейкстра с кучей: O((V + E) log V). Веса рёбер неотрицательные.
import heapq

INF = float("inf")
edges = {0: [(1, 4), (2, 1)], 1: [(3, 1)], 2: [(1, 2), (3, 5)], 3: [(4, 3)], 4: []}


def dijkstra(start):
    dist = {v: INF for v in edges}
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, v = heapq.heappop(heap)
        if d > dist[v]:
            continue  # устаревшая запись в куче
        for u, w in edges[v]:
            if d + w < dist[u]:
                dist[u] = d + w
                heapq.heappush(heap, (dist[u], u))
    return dist


dist = dijkstra(0)
print("Dijkstra from 0:", *(dist[v] for v in sorted(edges)))
