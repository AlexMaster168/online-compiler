// Поиск в глубину рекурсией: O(V + E).
val graph = listOf(listOf(1, 2), listOf(0, 3), listOf(0, 4), listOf(1, 5), listOf(2, 5), listOf(3, 4))

fun dfs(v: Int, visited: MutableSet<Int> = mutableSetOf(), order: MutableList<Int> = mutableListOf()): List<Int> {
    visited += v
    order += v
    for (u in graph[v]) if (u !in visited) dfs(u, visited, order)
    return order
}

fun main() {
    println("DFS order: " + dfs(0).joinToString(" "))
}
