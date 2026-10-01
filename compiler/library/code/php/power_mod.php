<?php
// Быстрое возведение в степень: O(log n).
const MOD = 1000000007;

function powerMod(int $base, int $exp, int $mod): int
{
    $result = 1;
    $base %= $mod;
    while ($exp > 0) {
        if ($exp & 1) {
            $result = $result * $base % $mod;
        }
        $base = $base * $base % $mod;
        $exp >>= 1;
    }
    return $result;
}

echo "2^30 mod " . MOD . " = " . powerMod(2, 30, MOD) . "\n";
echo "3^200 mod " . MOD . " = " . powerMod(3, 200, MOD) . "\n";
