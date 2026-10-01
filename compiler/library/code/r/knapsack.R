# Рюкзак 0/1: dp[c + 1] — лучшая ценность при вместимости c; c идёт сверху вниз.
knapsack <- function(weights, values, capacity) {
  dp <- rep(0, capacity + 1)
  for (i in seq_along(weights)) {
    for (c in capacity:weights[i]) {
      dp[c + 1] <- max(dp[c + 1], dp[c - weights[i] + 1] + values[i])
    }
  }
  dp[capacity + 1]
}

cat("Knapsack max value:", knapsack(c(1, 3, 4, 5), c(1, 4, 5, 7), 7), "\n")
