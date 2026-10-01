#!/usr/bin/env bash
# Факториал рекурсией. Результат — в глобальной переменной: $(...) на каждом уровне
# порождал бы подоболочку (fork), а так рекурсия идёт в одном процессе. 20! — предел 64-бит.
factorial() {
    local n=$1
    if ((n <= 1)); then
        result=1
    else
        factorial $((n - 1))
        result=$((n * result))
    fi
}

factorial 10
echo "10! = $result"
factorial 20
echo "20! = $result"
