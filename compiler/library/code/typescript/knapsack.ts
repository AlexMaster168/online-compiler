// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c.
function knapsack(weights: number[], values: number[], capacity: number): number {
  const dp = new Array<number>(capacity + 1).fill(0);
  weights.forEach((w, i) => {
    for (let c = capacity; c >= w; c--) dp[c] = Math.max(dp[c], dp[c - w] + values[i]);
  });
  return dp[capacity];
}

console.log("Knapsack max value: " + knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7));
