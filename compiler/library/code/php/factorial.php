<?php
// Факториал рекурсией. 20! — предел 64-битного int в PHP.
function factorial(int $n): int
{
    return $n <= 1 ? 1 : $n * factorial($n - 1);
}

echo "10! = " . factorial(10) . "\n";
echo "20! = " . factorial(20) . "\n";
