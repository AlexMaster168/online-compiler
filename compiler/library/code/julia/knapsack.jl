# Рюкзак 0/1: dp[c+1] — лучшая ценность при вместимости c; c идёт сверху вниз.
function knapsack(weights, values, capacity)
    dp = zeros(Int, capacity + 1)
    for (w, v) in zip(weights, values), c in capacity:-1:w
        dp[c+1] = max(dp[c+1], dp[c-w+1] + v)
    end
    dp[end]
end

println("Knapsack max value: ", knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7))
