<?php
// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
function bubbleSort(array $a): array
{
    $n = count($a);
    for ($i = 0; $i < $n - 1; $i++) {
        $swapped = false;
        for ($j = 0; $j < $n - 1 - $i; $j++) {
            if ($a[$j] > $a[$j + 1]) {
                [$a[$j], $a[$j + 1]] = [$a[$j + 1], $a[$j]];
                $swapped = true;
            }
        }
        if (!$swapped) {
            break;
        }
    }
    return $a;  // массивы в PHP передаются по значению — оригинал не меняется
}

echo "Sorted: " . implode(" ", bubbleSort([5, 2, 9, 1, 5, 6])) . "\n";
