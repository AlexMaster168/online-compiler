// Решето Эратосфена: O(n log log n).
List<int> sieve(int n) {
  final isPrime = List.filled(n + 1, true)
    ..[0] = false
    ..[1] = false;
  for (var p = 2; p * p <= n; p++) {
    if (!isPrime[p]) continue;
    for (var k = p * p; k <= n; k += p) {
      isPrime[k] = false;
    }
  }
  return [for (var i = 0; i <= n; i++) if (isPrime[i]) i];
}

void main() {
  print('Primes up to 50: ${sieve(50).join(' ')}');
}
