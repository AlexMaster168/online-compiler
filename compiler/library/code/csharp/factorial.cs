// Факториал рекурсией. 20! — предел long; дальше нужен System.Numerics.BigInteger.
using System;

class Program
{
    static long Factorial(int n) => n <= 1 ? 1 : n * Factorial(n - 1);

    static void Main()
    {
        Console.WriteLine($"10! = {Factorial(10)}");
        Console.WriteLine($"20! = {Factorial(20)}");
    }
}
