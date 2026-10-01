# Числа Фибоначчи итеративно. F(50) > 2^31 — считаем в double, он точен до 2^53.
fib <- function(n) {
  a <- 0
  b <- 1
  for (i in seq_len(n)) {
    t <- a + b
    a <- b
    b <- t
  }
  a
}

cat("Fibonacci:", sapply(0:14, fib), "\n")
cat("F(50) =", format(fib(50), scientific = FALSE), "\n")
