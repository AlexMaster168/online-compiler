#!/usr/bin/env bash
# Бинарный поиск: O(log n). Результат — в stdout функции, -1 если не нашли.
arr=(1 3 5 7 9 11 13 15 17 19)

binary_search() {
    local target=$1 lo=0 hi=$((${#arr[@]} - 1)) mid
    while ((lo <= hi)); do
        mid=$(((lo + hi) / 2))
        if ((arr[mid] == target)); then echo "$mid"; return; fi
        if ((arr[mid] < target)); then lo=$((mid + 1)); else hi=$((mid - 1)); fi
    done
    echo -1
}

for target in 7 4; do
    i=$(binary_search "$target")
    if ((i >= 0)); then echo "Found $target at index $i"; else echo "$target not found"; fi
done
