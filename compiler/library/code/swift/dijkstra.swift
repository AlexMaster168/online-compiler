// Дейкстра за O(V^2): каждый раз берём ближайшую непосещённую вершину.
let edges: [[(to: Int, w: Int)]] = [[(1, 4), (2, 1)], [(3, 1)], [(1, 2), (3, 5)], [(4, 3)], []]
var dist = [Int](repeating: Int.max, count: edges.count)
var done = [Bool](repeating: false, count: edges.count)
dist[0] = 0
for _ in edges.indices {
    guard let v = edges.indices.filter({ !done[$0] }).min(by: { dist[$0] < dist[$1] }), dist[v] != Int.max else { break }
    done[v] = true
    for e in edges[v] where dist[v] + e.w < dist[e.to] {
        dist[e.to] = dist[v] + e.w
    }
}
print("Dijkstra from 0:", dist.map(String.init).joined(separator: " "))
