#!/usr/bin/env bash
# Быстрая сортировка (разбиение Ломуто). Функции bash не возвращают значения — индекс опоры кладём в глобальную.
a=(10 7 8 9 1 5 3)

partition() {
    local lo=$1 hi=$2 pivot=${a[$2]} i=$1 j tmp
    for ((j = lo; j < hi; j++)); do
        if ((a[j] < pivot)); then
            tmp=${a[i]}; a[i]=${a[j]}; a[j]=$tmp
            ((i++))
        fi
    done
    tmp=${a[i]}; a[i]=${a[hi]}; a[hi]=$tmp
    pivot_index=$i
}

quick_sort() {
    local lo=$1 hi=$2 p
    ((lo >= hi)) && return
    partition "$lo" "$hi"
    p=$pivot_index
    quick_sort "$lo" $((p - 1))
    quick_sort $((p + 1)) "$hi"
}

quick_sort 0 $((${#a[@]} - 1))
echo "Sorted: ${a[*]}"
