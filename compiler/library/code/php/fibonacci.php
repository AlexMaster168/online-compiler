<?php
// Числа Фибоначчи генератором (yield): числа считаются по требованию.
function fibonacci(): Generator
{
    [$a, $b] = [0, 1];
    while (true) {
        yield $a;
        [$a, $b] = [$b, $a + $b];
    }
}

$first = [];
foreach (fibonacci() as $i => $f) {
    if ($i < 15) {
        $first[] = $f;
    }
    if ($i === 50) {
        $f50 = $f;
        break;
    }
}
echo "Fibonacci: " . implode(" ", $first) . "\n";
echo "F(50) = $f50\n";
