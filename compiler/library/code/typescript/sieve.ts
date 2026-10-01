// Решето Эратосфена: O(n log log n).
function sieve(n: number): number[] {
  const isPrime: boolean[] = new Array(n + 1).fill(true);
  isPrime[0] = isPrime[1] = false;
  for (let p = 2; p * p <= n; p++) {
    if (!isPrime[p]) continue;
    for (let k = p * p; k <= n; k += p) isPrime[k] = false;
  }
  return isPrime.flatMap((prime, i) => (prime ? [i] : []));
}

console.log("Primes up to 50: " + sieve(50).join(" "));
