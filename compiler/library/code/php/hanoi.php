<?php
// Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
function hanoi(int $n, string $source, string $spare, string $target): int
{
    if ($n === 0) {
        return 0;
    }
    $before = hanoi($n - 1, $source, $target, $spare);
    echo "Move disk $n from $source to $target\n";
    return $before + 1 + hanoi($n - 1, $spare, $source, $target);
}

echo "Total moves: " . hanoi(3, "A", "B", "C") . "\n";
