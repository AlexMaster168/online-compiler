# Решето Эратосфена: вычёркиваем кратные векторной операцией seq(p * p, n, by = p).
sieve <- function(n) {
  is_prime <- rep(TRUE, n)
  is_prime[1] <- FALSE
  for (p in 2:floor(sqrt(n))) {
    if (is_prime[p]) is_prime[seq(p * p, n, by = p)] <- FALSE
  }
  which(is_prime)
}

cat("Primes up to 50:", sieve(50), "\n")
