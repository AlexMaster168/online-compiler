// Решето Эратосфена: O(n log log n).
fun sieve(n: Int): List<Int> {
    val isPrime = BooleanArray(n + 1) { it >= 2 }
    var p = 2
    while (p * p <= n) {
        if (isPrime[p]) {
            for (k in p * p..n step p) isPrime[k] = false
        }
        p++
    }
    return (0..n).filter { isPrime[it] }
}

fun main() {
    println("Primes up to 50: " + sieve(50).joinToString(" "))
}
