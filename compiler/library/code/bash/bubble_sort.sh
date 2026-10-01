#!/usr/bin/env bash
# Сортировка пузырьком: O(n^2). Массив — глобальный, (( )) — целочисленная арифметика.
a=(5 2 9 1 5 6)
n=${#a[@]}
for ((i = 0; i < n - 1; i++)); do
    swapped=0
    for ((j = 0; j < n - 1 - i; j++)); do
        if ((a[j] > a[j + 1])); then
            tmp=${a[j]}
            a[j]=${a[j + 1]}
            a[j + 1]=$tmp
            swapped=1
        fi
    done
    ((swapped)) || break
done
echo "Sorted: ${a[*]}"
