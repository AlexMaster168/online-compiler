// Числа Фибоначчи: std.range.recurrence — последовательность по рекуррентной формуле.
import std.range : drop, recurrence, take;
import std.stdio;

void main()
{
    auto fib = recurrence!((a, n) => a[n - 1] + a[n - 2])(0L, 1L);
    writefln("Fibonacci: %(%s %)", fib.take(15));
    writefln("F(50) = %d", fib.drop(50).front);
}
