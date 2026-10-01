# Дейкстра за O(V^2) на матрице весов (0 — нет ребра).
w <- matrix(c(
  0, 4, 1, 0, 0,
  0, 0, 0, 1, 0,
  0, 2, 0, 5, 0,
  0, 0, 0, 0, 3,
  0, 0, 0, 0, 0
), nrow = 5, byrow = TRUE)
n <- nrow(w)
dist <- rep(Inf, n)
done <- rep(FALSE, n)
dist[1] <- 0
for (step in 1:n) {
  candidates <- which(!done)
  v <- candidates[which.min(dist[candidates])]
  if (is.infinite(dist[v])) break
  done[v] <- TRUE
  for (u in which(w[v, ] > 0)) dist[u] <- min(dist[u], dist[v] + w[v, u])
}
cat("Dijkstra from 0:", dist, "\n")
