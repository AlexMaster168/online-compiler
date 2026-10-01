#!/usr/bin/env bash
# Поиск в глубину рекурсией. local u обязателен — иначе рекурсия затрёт переменную цикла.
graph=("1 2" "0 3" "0 4" "1 5" "2 5" "3 4")
declare -a visited
order=()

dfs() {
    local v=$1 u
    visited[v]=1
    order+=("$v")
    for u in ${graph[v]}; do
        ((visited[u])) || dfs "$u"
    done
}

dfs 0
echo "DFS order: ${order[*]}"
