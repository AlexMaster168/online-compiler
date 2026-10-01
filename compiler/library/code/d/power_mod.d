// Быстрое возведение в степень: O(log n).
import std.stdio;

enum long MOD = 1_000_000_007;

long powerMod(long base, long exp, long m)
{
    long result = 1;
    base %= m;
    while (exp > 0)
    {
        if (exp & 1)
            result = result * base % m;
        base = base * base % m;
        exp >>= 1;
    }
    return result;
}

void main()
{
    writefln("2^30 mod %d = %d", MOD, powerMod(2, 30, MOD));
    writefln("3^200 mod %d = %d", MOD, powerMod(3, 200, MOD));
}
