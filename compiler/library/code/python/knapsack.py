# Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c. Идём по c сверху вниз, чтобы брать предмет один раз.


def knapsack(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[capacity]


print("Knapsack max value:", knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7))
