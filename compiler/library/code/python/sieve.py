# Решето Эратосфена: O(n log log n). Вычёркивать кратные p можно начинать с p*p.


def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    p = 2
    while p * p <= n:
        if is_prime[p]:
            for k in range(p * p, n + 1, p):
                is_prime[k] = False
        p += 1
    return [i for i, prime in enumerate(is_prime) if prime]


print("Primes up to 50:", *sieve(50))
