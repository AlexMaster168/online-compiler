#!/usr/bin/env bash
# Сортировка слиянием: сортируем отрезок [lo, hi) глобального массива, временный буфер — tmp.
a=(38 27 43 3 9 82 10)

merge_sort() {
    local lo=$1 hi=$2
    ((hi - lo < 2)) && return
    local mid=$(((lo + hi) / 2))
    merge_sort "$lo" "$mid"
    merge_sort "$mid" "$hi"
    local i=$lo j=$mid k
    local -a tmp=()
    while ((i < mid && j < hi)); do
        if ((a[i] <= a[j])); then tmp+=("${a[i++]}"); else tmp+=("${a[j++]}"); fi
    done
    while ((i < mid)); do tmp+=("${a[i++]}"); done
    while ((j < hi)); do tmp+=("${a[j++]}"); done
    for ((k = 0; k < hi - lo; k++)); do a[lo + k]=${tmp[k]}; done
}

merge_sort 0 ${#a[@]}
echo "Sorted: ${a[*]}"
