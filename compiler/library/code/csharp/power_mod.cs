// Быстрое возведение в степень: O(log n).
using System;

class Program
{
    const long Mod = 1_000_000_007;

    static long PowerMod(long b, long exp, long mod)
    {
        long result = 1;
        b %= mod;
        while (exp > 0)
        {
            if ((exp & 1) == 1) result = result * b % mod;
            b = b * b % mod;
            exp >>= 1;
        }
        return result;
    }

    static void Main()
    {
        Console.WriteLine($"2^30 mod {Mod} = {PowerMod(2, 30, Mod)}");
        Console.WriteLine($"3^200 mod {Mod} = {PowerMod(3, 200, Mod)}");
    }
}
