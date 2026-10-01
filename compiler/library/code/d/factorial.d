// Факториал рекурсией. ulong — 64 бита, 20! помещается.
import std.stdio;

ulong factorial(uint n) => n <= 1 ? 1 : n * factorial(n - 1);

void main()
{
    writefln("10! = %d", factorial(10));
    writefln("20! = %d", factorial(20));
}
