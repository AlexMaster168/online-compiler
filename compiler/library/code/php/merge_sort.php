<?php
// Сортировка слиянием: всегда O(n log n), стабильная.
function mergeSort(array $a): array
{
    if (count($a) <= 1) {
        return $a;
    }
    $mid = intdiv(count($a), 2);
    $left = mergeSort(array_slice($a, 0, $mid));
    $right = mergeSort(array_slice($a, $mid));
    $merged = [];
    $i = $j = 0;
    while ($i < count($left) && $j < count($right)) {
        $merged[] = $left[$i] <= $right[$j] ? $left[$i++] : $right[$j++];
    }
    return array_merge($merged, array_slice($left, $i), array_slice($right, $j));
}

echo "Sorted: " . implode(" ", mergeSort([38, 27, 43, 3, 9, 82, 10])) . "\n";
