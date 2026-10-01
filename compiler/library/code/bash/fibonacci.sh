#!/usr/bin/env bash
# Числа Фибоначчи итеративно. Арифметика bash 64-битная — F(50) помещается.
a=0 b=1
first=()
for ((i = 0; i <= 50; i++)); do
    ((i < 15)) && first+=("$a")
    ((i == 50)) && f50=$a
    t=$((a + b)); a=$b; b=$t
done
echo "Fibonacci: ${first[*]}"
echo "F(50) = $f50"
