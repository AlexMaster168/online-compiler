# Поиск в глубину рекурсией: O(V + E). Соседей обходим по возрастанию.
graph = {0: [1, 2], 1: [0, 3], 2: [0, 4], 3: [1, 5], 4: [2, 5], 5: [3, 4]}


def dfs(v, visited, order):
    visited.add(v)
    order.append(v)
    for u in graph[v]:
        if u not in visited:
            dfs(u, visited, order)
    return order


print("DFS order:", *dfs(0, set(), []))
