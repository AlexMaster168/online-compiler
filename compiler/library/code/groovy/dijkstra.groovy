// Дейкстра с PriorityQueue из Java: в очереди пары [расстояние, вершина].
def graph = [[[1, 4], [2, 1]], [[3, 1]], [[1, 2], [3, 5]], [[4, 3]], []]
def dist = [Integer.MAX_VALUE] * graph.size()
dist[0] = 0
def pq = new PriorityQueue<List<Integer>>({ x, y -> x[0] <=> y[0] } as Comparator)
pq << [0, 0]
while (pq) {
    def (d, v) = pq.poll()
    if (d > dist[v]) continue  // устаревшая запись
    graph[v].each { u, w ->
        if (d + w < dist[u]) {
            dist[u] = d + w
            pq << [dist[u], u]
        }
    }
}
println "Dijkstra from 0: ${dist.join(' ')}"
