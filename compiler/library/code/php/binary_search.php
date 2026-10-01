<?php
// Бинарный поиск: O(log n), массив обязан быть отсортирован.
function binarySearch(array $a, int $target): int
{
    $lo = 0;
    $hi = count($a) - 1;
    while ($lo <= $hi) {
        $mid = intdiv($lo + $hi, 2);
        if ($a[$mid] === $target) {
            return $mid;
        }
        if ($a[$mid] < $target) {
            $lo = $mid + 1;
        } else {
            $hi = $mid - 1;
        }
    }
    return -1;
}

$arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
foreach ([7, 4] as $target) {
    $i = binarySearch($arr, $target);
    echo $i >= 0 ? "Found $target at index $i\n" : "$target not found\n";
}
