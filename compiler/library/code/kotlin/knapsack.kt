// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
fun knapsack(weights: IntArray, values: IntArray, capacity: Int): Int {
    val dp = IntArray(capacity + 1)
    for (i in weights.indices) {
        for (c in capacity downTo weights[i]) dp[c] = maxOf(dp[c], dp[c - weights[i]] + values[i])
    }
    return dp[capacity]
}

fun main() {
    println("Knapsack max value: " + knapsack(intArrayOf(1, 3, 4, 5), intArrayOf(1, 4, 5, 7), 7))
}
