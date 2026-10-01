// НОД по Евклиду: gcd(a, b) = gcd(b, a % b). (В std.numeric есть gcd — пишем свой.)
import std.stdio;

long gcd(long a, long b) => b == 0 ? a : gcd(b, a % b);
long lcm(long a, long b) => a / gcd(a, b) * b;

void main()
{
    writefln("GCD(48, 18) = %d", gcd(48, 18));
    writefln("LCM(48, 18) = %d", lcm(48, 18));
}
