# Быстрое возведение в степень. Произведение двух чисел < 1e9+7 не влезает точно в double,
# поэтому умножаем «по частям» (mul_mod) — разбиваем множитель на 2^15-блоки.
MOD <- 1000000007

mul_mod <- function(a, b, m) {
  result <- 0
  while (b > 0) {
    chunk <- b %% 32768
    result <- (result + (a * chunk) %% m) %% m
    a <- (a * 32768) %% m
    b <- b %/% 32768
  }
  result
}

power_mod <- function(base, exp, m) {
  result <- 1
  base <- base %% m
  while (exp > 0) {
    if (exp %% 2 == 1) result <- mul_mod(result, base, m)
    base <- mul_mod(base, base, m)
    exp <- exp %/% 2
  }
  result
}

cat(sprintf("2^30 mod %.0f = %.0f\n", MOD, power_mod(2, 30, MOD)))
cat(sprintf("3^200 mod %.0f = %.0f\n", MOD, power_mod(3, 200, MOD)))
