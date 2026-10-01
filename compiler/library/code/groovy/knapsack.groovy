// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; downto — цикл сверху вниз.
int knapsack(List<List<Integer>> items, int capacity) {
    def dp = [0] * (capacity + 1)
    items.each { w, v ->
        capacity.downto(w) { c -> dp[c] = Math.max(dp[c], dp[c - w] + v) }
    }
    dp[capacity]
}

println "Knapsack max value: ${knapsack([[1, 1], [3, 4], [4, 5], [5, 7]], 7)}"
