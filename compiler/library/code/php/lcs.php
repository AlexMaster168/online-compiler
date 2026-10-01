<?php
// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
function lcs(string $a, string $b): int
{
    $n = strlen($a);
    $m = strlen($b);
    $dp = array_fill(0, $n + 1, array_fill(0, $m + 1, 0));
    for ($i = 1; $i <= $n; $i++) {
        for ($j = 1; $j <= $m; $j++) {
            $dp[$i][$j] = $a[$i - 1] === $b[$j - 1]
                ? $dp[$i - 1][$j - 1] + 1
                : max($dp[$i - 1][$j], $dp[$i][$j - 1]);
        }
    }
    return $dp[$n][$m];
}

echo "LCS(ABCBDAB, BDCABA) = " . lcs("ABCBDAB", "BDCABA") . "\n";
