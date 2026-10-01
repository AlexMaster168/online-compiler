// Решето Эратосфена: O(n log log n).
using System;
using System.Collections.Generic;

class Program
{
    static List<int> Sieve(int n)
    {
        var composite = new bool[n + 1];
        var primes = new List<int>();
        for (int p = 2; p <= n; p++)
        {
            if (composite[p]) continue;
            primes.Add(p);
            for (int k = p * p; k <= n; k += p) composite[k] = true;
        }
        return primes;
    }

    static void Main() => Console.WriteLine("Primes up to 50: " + string.Join(" ", Sieve(50)));
}
