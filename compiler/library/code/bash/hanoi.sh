#!/usr/bin/env bash
# Ханойские башни: 2^n - 1 ходов. Счётчик — глобальный (подстановка $(...) запускала бы подоболочку).
moves=0

hanoi() {
    local n=$1 source=$2 spare=$3 target=$4
    ((n == 0)) && return
    hanoi $((n - 1)) "$source" "$target" "$spare"
    echo "Move disk $n from $source to $target"
    ((moves++))
    hanoi $((n - 1)) "$spare" "$source" "$target"
}

hanoi 3 A B C
echo "Total moves: $moves"
