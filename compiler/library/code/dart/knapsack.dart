// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
import 'dart:math';

int knapsack(List<int> weights, List<int> values, int capacity) {
  final dp = List.filled(capacity + 1, 0);
  for (var i = 0; i < weights.length; i++) {
    for (var c = capacity; c >= weights[i]; c--) {
      dp[c] = max(dp[c], dp[c - weights[i]] + values[i]);
    }
  }
  return dp[capacity];
}

void main() {
  print('Knapsack max value: ${knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7)}');
}
