#!/usr/bin/env bash
# Наибольшая общая подпоследовательность: двумерная таблица в ассоциативном массиве с ключом "i,j".
a=ABCBDAB
b=BDCABA
declare -A dp
for ((i = 0; i <= ${#a}; i++)); do
    for ((j = 0; j <= ${#b}; j++)); do
        if ((i == 0 || j == 0)); then
            dp[$i,$j]=0
        elif [[ ${a:i-1:1} == "${b:j-1:1}" ]]; then
            dp[$i,$j]=$((dp[$((i - 1)),$((j - 1))] + 1))
        else
            up=${dp[$((i - 1)),$j]} left=${dp[$i,$((j - 1))]}
            dp[$i,$j]=$((up > left ? up : left))
        fi
    done
done
echo "LCS($a, $b) = ${dp[${#a},${#b}]}"
