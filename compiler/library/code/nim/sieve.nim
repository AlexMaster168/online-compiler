# Решето Эратосфена: countup(from, to, step) — цикл с шагом.
import std/strutils

proc sieve(n: int): seq[int] =
  var composite = newSeq[bool](n + 1)
  for p in 2 .. n:
    if composite[p]: continue
    result.add p
    for k in countup(p * p, n, p):
      composite[k] = true

echo "Primes up to 50: ", sieve(50).join(" ")
