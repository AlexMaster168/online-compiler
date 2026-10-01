// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
#include <algorithm>
#include <iostream>
#include <vector>

int knapsack(const std::vector<int>& weights, const std::vector<int>& values, int capacity) {
    std::vector<int> dp(capacity + 1, 0);
    for (std::size_t i = 0; i < weights.size(); ++i)
        for (int c = capacity; c >= weights[i]; --c) dp[c] = std::max(dp[c], dp[c - weights[i]] + values[i]);
    return dp[capacity];
}

int main() { std::cout << "Knapsack max value: " << knapsack({1, 3, 4, 5}, {1, 4, 5, 7}, 7) << '\n'; }
