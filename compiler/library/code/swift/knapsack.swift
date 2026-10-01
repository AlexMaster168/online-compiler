// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
func knapsack(_ weights: [Int], _ values: [Int], _ capacity: Int) -> Int {
    var dp = [Int](repeating: 0, count: capacity + 1)
    for (w, v) in zip(weights, values) {
        for c in stride(from: capacity, through: w, by: -1) {
            dp[c] = max(dp[c], dp[c - w] + v)
        }
    }
    return dp[capacity]
}

print("Knapsack max value:", knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7))
