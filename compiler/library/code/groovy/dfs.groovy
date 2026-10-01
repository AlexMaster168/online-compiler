// Поиск в глубину рекурсивным замыканием: замыкание ссылается само на себя через переменную.
def graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]]
def visited = [] as Set
def order = []
def dfs
dfs = { int v ->
    visited << v
    order << v
    graph[v].each { u -> if (!(u in visited)) dfs(u) }
}

dfs(0)
println "DFS order: ${order.join(' ')}"
