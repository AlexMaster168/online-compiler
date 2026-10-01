# Поиск в ширину: очередь — вектор, вершины 0..5 хранятся со сдвигом +1 (индексы R с единицы).
graph <- list(c(1, 2), c(0, 3), c(0, 4), c(1, 5), c(2, 5), c(3, 4))
dist <- rep(-1, 6)
dist[1] <- 0
queue <- c(0)
order <- c()
while (length(queue) > 0) {
  v <- queue[1]
  queue <- queue[-1]
  order <- c(order, v)
  for (u in graph[[v + 1]]) {
    if (dist[u + 1] == -1) {
      dist[u + 1] <- dist[v + 1] + 1
      queue <- c(queue, u)
    }
  }
}
cat("BFS order:", order, "\n")
cat("Distances:", dist, "\n")
