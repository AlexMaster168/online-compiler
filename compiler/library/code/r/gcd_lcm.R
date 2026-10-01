# НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). %% — остаток, %/% — целочисленное деление.
gcd <- function(a, b) if (b == 0) a else gcd(b, a %% b)
lcm <- function(a, b) a %/% gcd(a, b) * b

cat(sprintf("GCD(48, 18) = %d\n", gcd(48L, 18L)))
cat(sprintf("LCM(48, 18) = %d\n", lcm(48L, 18L)))
