<?php
// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
function knapsack(array $weights, array $values, int $capacity): int
{
    $dp = array_fill(0, $capacity + 1, 0);
    foreach ($weights as $i => $w) {
        for ($c = $capacity; $c >= $w; $c--) {
            $dp[$c] = max($dp[$c], $dp[$c - $w] + $values[$i]);
        }
    }
    return $dp[$capacity];
}

echo "Knapsack max value: " . knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7) . "\n";
