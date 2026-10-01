// Решето Эратосфена: step — шаг по диапазону.
def sieve(int n) {
    def isPrime = [true] * (n + 1)
    isPrime[0] = isPrime[1] = false
    for (p in 2..n) {
        if (isPrime[p] && p * p <= n) {
            (p * p).step(n + 1, p) { isPrime[it] = false }
        }
    }
    (0..n).findAll { isPrime[it] }
}

println "Primes up to 50: ${sieve(50).join(' ')}"
