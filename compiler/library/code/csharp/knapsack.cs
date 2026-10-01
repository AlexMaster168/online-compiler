// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
using System;

class Program
{
    static int Knapsack(int[] weights, int[] values, int capacity)
    {
        var dp = new int[capacity + 1];
        for (int i = 0; i < weights.Length; i++)
            for (int c = capacity; c >= weights[i]; c--)
                dp[c] = Math.Max(dp[c], dp[c - weights[i]] + values[i]);
        return dp[capacity];
    }

    static void Main() => Console.WriteLine("Knapsack max value: " + Knapsack(new[] { 1, 3, 4, 5 }, new[] { 1, 4, 5, 7 }, 7));
}
