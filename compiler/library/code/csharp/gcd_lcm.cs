// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
using System;

class Program
{
    static long Gcd(long a, long b) => b == 0 ? a : Gcd(b, a % b);
    static long Lcm(long a, long b) => a / Gcd(a, b) * b;

    static void Main()
    {
        Console.WriteLine($"GCD(48, 18) = {Gcd(48, 18)}");
        Console.WriteLine($"LCM(48, 18) = {Lcm(48, 18)}");
    }
}
