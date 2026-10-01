# Наибольшая общая подпоследовательность: матрица dp размером (n+1) x (m+1).
lcs <- function(a, b) {
  x <- strsplit(a, "")[[1]]
  y <- strsplit(b, "")[[1]]
  dp <- matrix(0, length(x) + 1, length(y) + 1)
  for (i in seq_along(x)) {
    for (j in seq_along(y)) {
      dp[i + 1, j + 1] <- if (x[i] == y[j]) dp[i, j] + 1 else max(dp[i, j + 1], dp[i + 1, j])
    }
  }
  dp[length(x) + 1, length(y) + 1]
}

cat("LCS(ABCBDAB, BDCABA) =", lcs("ABCBDAB", "BDCABA"), "\n")
