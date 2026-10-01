# Поиск в глубину рекурсией. <<- меняет переменную из внешнего окружения.
graph <- list(c(1, 2), c(0, 3), c(0, 4), c(1, 5), c(2, 5), c(3, 4))
visited <- rep(FALSE, 6)
order <- c()

dfs <- function(v) {
  visited[v + 1] <<- TRUE
  order <<- c(order, v)
  for (u in graph[[v + 1]]) {
    if (!visited[u + 1]) dfs(u)
  }
}

dfs(0)
cat("DFS order:", order, "\n")
