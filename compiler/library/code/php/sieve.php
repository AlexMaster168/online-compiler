<?php
// Решето Эратосфена: O(n log log n).
function sieve(int $n): array
{
    $isPrime = array_fill(0, $n + 1, true);
    $isPrime[0] = $isPrime[1] = false;
    for ($p = 2; $p * $p <= $n; $p++) {
        if (!$isPrime[$p]) {
            continue;
        }
        for ($k = $p * $p; $k <= $n; $k += $p) {
            $isPrime[$k] = false;
        }
    }
    return array_keys(array_filter($isPrime));
}

echo "Primes up to 50: " . implode(" ", sieve(50)) . "\n";
