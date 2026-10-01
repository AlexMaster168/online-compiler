// Поиск в глубину вложенной рекурсивной функцией: O(V + E).
let graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]]
var visited = Set<Int>()
var order: [Int] = []

func dfs(_ v: Int) {
    visited.insert(v)
    order.append(v)
    for u in graph[v] where !visited.contains(u) {
        dfs(u)
    }
}

dfs(0)
print("DFS order:", order.map(String.init).joined(separator: " "))
