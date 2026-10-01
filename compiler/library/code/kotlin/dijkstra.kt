// Дейкстра с java.util.PriorityQueue: O((V + E) log V).
import java.util.PriorityQueue

fun main() {
    val graph = listOf(listOf(1 to 4, 2 to 1), listOf(3 to 1), listOf(1 to 2, 3 to 5), listOf(4 to 3), emptyList())
    val dist = IntArray(graph.size) { Int.MAX_VALUE }
    dist[0] = 0
    val pq = PriorityQueue<Pair<Int, Int>>(compareBy { it.first })
    pq += 0 to 0
    while (pq.isNotEmpty()) {
        val (d, v) = pq.poll()
        if (d > dist[v]) continue // устаревшая запись
        for ((u, w) in graph[v]) {
            if (d + w < dist[u]) {
                dist[u] = d + w
                pq += dist[u] to u
            }
        }
    }
    println("Dijkstra from 0: " + dist.joinToString(" "))
}
