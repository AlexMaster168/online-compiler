# Бинарный поиск: O(log n). Возвращаем индекс с нуля, как в других языках.
binary_search <- function(a, target) {
  lo <- 1
  hi <- length(a)
  while (lo <= hi) {
    mid <- (lo + hi) %/% 2
    if (a[mid] == target) return(mid - 1)
    if (a[mid] < target) lo <- mid + 1 else hi <- mid - 1
  }
  NA
}

arr <- c(1, 3, 5, 7, 9, 11, 13, 15, 17, 19)
for (target in c(7, 4)) {
  i <- binary_search(arr, target)
  if (is.na(i)) cat(target, "not found\n") else cat(sprintf("Found %d at index %d\n", target, i))
}
