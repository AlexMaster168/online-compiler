#!/usr/bin/env bash
# НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
gcd() {
    local a=$1 b=$2 t
    while ((b != 0)); do
        t=$((a % b)); a=$b; b=$t
    done
    echo "$a"
}

lcm() {
    echo $(($1 / $(gcd "$1" "$2") * $2))
}

echo "GCD(48, 18) = $(gcd 48 18)"
echo "LCM(48, 18) = $(lcm 48 18)"
