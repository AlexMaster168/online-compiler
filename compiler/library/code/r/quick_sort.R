# Быстрая сортировка: опора и векторные фильтры a[a < pivot] — в R это естественнее, чем Ломуто.
quick_sort <- function(a) {
  if (length(a) <= 1) return(a)
  pivot <- a[1]
  rest <- a[-1]
  c(quick_sort(rest[rest < pivot]), pivot, quick_sort(rest[rest >= pivot]))
}

cat("Sorted:", quick_sort(c(10, 7, 8, 9, 1, 5, 3)), "\n")
