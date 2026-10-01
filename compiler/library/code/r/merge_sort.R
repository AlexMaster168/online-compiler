# Сортировка слиянием: всегда O(n log n), стабильная.
merge_sort <- function(a) {
  if (length(a) <= 1) return(a)
  mid <- length(a) %/% 2
  left <- merge_sort(a[1:mid])
  right <- merge_sort(a[(mid + 1):length(a)])
  merged <- numeric(0)
  i <- 1
  j <- 1
  while (i <= length(left) && j <= length(right)) {
    if (left[i] <= right[j]) {
      merged <- c(merged, left[i]); i <- i + 1
    } else {
      merged <- c(merged, right[j]); j <- j + 1
    }
  }
  c(merged, left[seq_len(length(left) - i + 1) + i - 1], right[seq_len(length(right) - j + 1) + j - 1])
}

cat("Sorted:", merge_sort(c(38, 27, 43, 3, 9, 82, 10)), "\n")
