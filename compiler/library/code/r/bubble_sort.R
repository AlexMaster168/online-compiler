# Сортировка пузырьком: O(n^2). Векторы в R индексируются с 1.
bubble_sort <- function(a) {
  n <- length(a)
  for (i in seq_len(n - 1)) {
    swapped <- FALSE
    for (j in seq_len(n - i)) {
      if (a[j] > a[j + 1]) {
        a[c(j, j + 1)] <- a[c(j + 1, j)]
        swapped <- TRUE
      }
    }
    if (!swapped) break
  }
  a  # R копирует вектор при изменении — оригинал снаружи не меняется
}

cat("Sorted:", bubble_sort(c(5, 2, 9, 1, 5, 6)), "\n")
