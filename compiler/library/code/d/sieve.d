// Решето Эратосфена: O(n log log n). iota — диапазон чисел с шагом.
import std.algorithm : filter;
import std.range : iota;
import std.stdio;

int[] sieve(int n)
{
    auto composite = new bool[n + 1];
    int[] primes;
    foreach (p; 2 .. n + 1)
    {
        if (composite[p])
            continue;
        primes ~= p;
        foreach (k; iota(p * p, n + 1, p))
            composite[k] = true;
    }
    return primes;
}

void main()
{
    writefln("Primes up to 50: %(%s %)", sieve(50));
}
