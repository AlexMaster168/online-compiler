#!/usr/bin/env bash
# Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
weights=(1 3 4 5)
values=(1 4 5 7)
capacity=7
dp=()
for ((c = 0; c <= capacity; c++)); do dp[c]=0; done
for i in "${!weights[@]}"; do
    w=${weights[i]}
    for ((c = capacity; c >= w; c--)); do
        take=$((dp[c - w] + values[i]))
        ((take > dp[c])) && dp[c]=$take
    done
done
echo "Knapsack max value: ${dp[capacity]}"
