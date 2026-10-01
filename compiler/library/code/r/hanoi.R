# Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
hanoi <- function(n, source, spare, target) {
  if (n == 0) return(0)
  before <- hanoi(n - 1, source, target, spare)
  cat(sprintf("Move disk %d from %s to %s\n", n, source, target))
  before + 1 + hanoi(n - 1, spare, source, target)
}

cat("Total moves:", hanoi(3, "A", "B", "C"), "\n")
