#!/usr/bin/env bash
# Решето Эратосфена: O(n log log n). Незаданный элемент массива в (( )) равен 0.
n=50
declare -a composite
primes=()
for ((p = 2; p <= n; p++)); do
    ((composite[p])) && continue
    primes+=("$p")
    for ((k = p * p; k <= n; k += p)); do composite[k]=1; done
done
echo "Primes up to $n: ${primes[*]}"
