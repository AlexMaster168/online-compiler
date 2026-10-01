// Ханойские башни: 2^n - 1 ходов.
using System;

class Program
{
    static int moves = 0;

    static void Hanoi(int n, char source, char spare, char target)
    {
        if (n == 0) return;
        Hanoi(n - 1, source, target, spare);
        Console.WriteLine($"Move disk {n} from {source} to {target}");
        moves++;
        Hanoi(n - 1, spare, source, target);
    }

    static void Main()
    {
        Hanoi(3, 'A', 'B', 'C');
        Console.WriteLine($"Total moves: {moves}");
    }
}
