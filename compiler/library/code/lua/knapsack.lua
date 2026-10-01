-- Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
local function knapsack(weights, values, capacity)
  local dp = {}
  for c = 0, capacity do dp[c] = 0 end
  for i, w in ipairs(weights) do
    for c = capacity, w, -1 do
      dp[c] = math.max(dp[c], dp[c - w] + values[i])
    end
  end
  return dp[capacity]
end

print("Knapsack max value: " .. knapsack({1, 3, 4, 5}, {1, 4, 5, 7}, 7))
