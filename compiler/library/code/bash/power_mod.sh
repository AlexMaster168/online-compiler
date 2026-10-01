#!/usr/bin/env bash
# Быстрое возведение в степень: O(log n).
MOD=1000000007

power_mod() {
    local base=$(($1 % $3)) exp=$2 mod=$3 result=1
    while ((exp > 0)); do
        ((exp & 1)) && result=$((result * base % mod))
        base=$((base * base % mod))
        ((exp >>= 1))
    done
    echo "$result"
}

echo "2^30 mod $MOD = $(power_mod 2 30 $MOD)"
echo "3^200 mod $MOD = $(power_mod 3 200 $MOD)"
