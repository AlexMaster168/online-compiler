// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз (foreach_reverse).
import std.algorithm : max;
import std.range : zip;
import std.stdio;

int knapsack(const int[] weights, const int[] values, int capacity)
{
    auto dp = new int[capacity + 1];
    foreach (item; zip(weights, values))
        foreach_reverse (c; item[0] .. capacity + 1)
            dp[c] = max(dp[c], dp[c - item[0]] + item[1]);
    return dp[capacity];
}

void main()
{
    writefln("Knapsack max value: %d", knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7));
}
