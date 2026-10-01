// Поиск в ширину: ArrayDeque из Java как очередь.
def graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]]
def dist = [-1] * graph.size()
def order = []
def queue = new ArrayDeque<Integer>([0])
dist[0] = 0
while (queue) {
    int v = queue.poll()
    order << v
    graph[v].each { u ->
        if (dist[u] == -1) {
            dist[u] = dist[v] + 1
            queue << u
        }
    }
}
println "BFS order: ${order.join(' ')}"
println "Distances: ${dist.join(' ')}"
