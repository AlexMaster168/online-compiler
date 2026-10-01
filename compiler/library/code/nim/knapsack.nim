# Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; countdown — цикл сверху вниз.
proc knapsack(items: openArray[(int, int)], capacity: int): int =
  var dp = newSeq[int](capacity + 1)
  for (w, v) in items:
    for c in countdown(capacity, w):
      dp[c] = max(dp[c], dp[c - w] + v)
  dp[capacity]

echo "Knapsack max value: ", knapsack([(1, 1), (3, 4), (4, 5), (5, 7)], 7)
