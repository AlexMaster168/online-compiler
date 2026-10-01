# Факториал рекурсией. 20! больше 2^53 — double хранит его точно только потому, что он делится на 2^18.
factorial_rec <- function(n) if (n <= 1) 1 else n * factorial_rec(n - 1)

cat("10! =", format(factorial_rec(10), scientific = FALSE), "\n")
cat("20! =", format(factorial_rec(20), scientific = FALSE, digits = 22), "\n")
