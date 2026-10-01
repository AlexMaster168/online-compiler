// Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
import std.stdio;

int hanoi(int n, char source, char spare, char target)
{
    if (n == 0)
        return 0;
    immutable before = hanoi(n - 1, source, target, spare);
    writefln("Move disk %d from %c to %c", n, source, target);
    return before + 1 + hanoi(n - 1, spare, source, target);
}

void main()
{
    writefln("Total moves: %d", hanoi(3, 'A', 'B', 'C'));
}
