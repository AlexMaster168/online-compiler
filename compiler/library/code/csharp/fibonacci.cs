// Числа Фибоначчи итеративно, O(n). F(50) не влезает в int — long.
using System;
using System.Linq;

class Program
{
    static long Fib(int n)
    {
        long a = 0, b = 1;
        for (int i = 0; i < n; i++) (a, b) = (b, a + b);
        return a;
    }

    static void Main()
    {
        Console.WriteLine("Fibonacci: " + string.Join(" ", Enumerable.Range(0, 15).Select(Fib)));
        Console.WriteLine($"F(50) = {Fib(50)}");
    }
}
