<?php
// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
function gcd(int $a, int $b): int
{
    return $b === 0 ? $a : gcd($b, $a % $b);
}

function lcm(int $a, int $b): int
{
    return intdiv($a, gcd($a, $b)) * $b;
}

echo "GCD(48, 18) = " . gcd(48, 18) . "\n";
echo "LCM(48, 18) = " . lcm(48, 18) . "\n";
