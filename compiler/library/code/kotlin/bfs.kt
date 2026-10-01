// Поиск в ширину: ArrayDeque, O(V + E).
val graph = listOf(listOf(1, 2), listOf(0, 3), listOf(0, 4), listOf(1, 5), listOf(2, 5), listOf(3, 4))

fun main() {
    val dist = IntArray(graph.size) { -1 }
    val order = mutableListOf<Int>()
    val queue = ArrayDeque(listOf(0))
    dist[0] = 0
    while (queue.isNotEmpty()) {
        val v = queue.removeFirst()
        order += v
        for (u in graph[v]) {
            if (dist[u] == -1) {
                dist[u] = dist[v] + 1
                queue.addLast(u)
            }
        }
    }
    println("BFS order: " + order.joinToString(" "))
    println("Distances: " + dist.joinToString(" "))
}
