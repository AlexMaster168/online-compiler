// Поиск в ширину: очередь на массиве с указателем головы, O(V + E).
let graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]]
var dist = [Int](repeating: -1, count: graph.count)
var order: [Int] = []
var queue = [0]
var head = 0
dist[0] = 0
while head < queue.count {
    let v = queue[head]
    head += 1
    order.append(v)
    for u in graph[v] where dist[u] == -1 {
        dist[u] = dist[v] + 1
        queue.append(u)
    }
}
print("BFS order:", order.map(String.init).joined(separator: " "))
print("Distances:", dist.map(String.init).joined(separator: " "))
