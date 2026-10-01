// Решето Эратосфена: O(n log log n). Вычёркивать кратные p можно начинать с p*p.
function sieve(n) {
  const isPrime = new Array(n + 1).fill(true);
  isPrime[0] = isPrime[1] = false;
  for (let p = 2; p * p <= n; p++) {
    if (!isPrime[p]) continue;
    for (let k = p * p; k <= n; k += p) isPrime[k] = false;
  }
  return isPrime.flatMap((prime, i) => (prime ? [i] : []));
}

console.log("Primes up to 50: " + sieve(50).join(" "));
