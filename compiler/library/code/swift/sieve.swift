// Решето Эратосфена: O(n log log n).
func sieve(_ n: Int) -> [Int] {
    var isPrime = [Bool](repeating: true, count: n + 1)
    isPrime[0] = false
    isPrime[1] = false
    var p = 2
    while p * p <= n {
        if isPrime[p] {
            for k in stride(from: p * p, through: n, by: p) { isPrime[k] = false }
        }
        p += 1
    }
    return isPrime.indices.filter { isPrime[$0] }
}

print("Primes up to 50:", sieve(50).map(String.init).joined(separator: " "))
