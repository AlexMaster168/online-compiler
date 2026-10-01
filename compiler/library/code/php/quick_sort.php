<?php
// Быстрая сортировка (разбиение Ломуто): массив передаём по ссылке (&$a), чтобы сортировать на месте.
function partition(array &$a, int $lo, int $hi): int
{
    $pivot = $a[$hi];
    $i = $lo;
    for ($j = $lo; $j < $hi; $j++) {
        if ($a[$j] < $pivot) {
            [$a[$i], $a[$j]] = [$a[$j], $a[$i]];
            $i++;
        }
    }
    [$a[$i], $a[$hi]] = [$a[$hi], $a[$i]];
    return $i;
}

function quickSort(array &$a, int $lo, int $hi): void
{
    if ($lo >= $hi) {
        return;
    }
    $p = partition($a, $lo, $hi);
    quickSort($a, $lo, $p - 1);
    quickSort($a, $p + 1, $hi);
}

$data = [10, 7, 8, 9, 1, 5, 3];
quickSort($data, 0, count($data) - 1);
echo "Sorted: " . implode(" ", $data) . "\n";
