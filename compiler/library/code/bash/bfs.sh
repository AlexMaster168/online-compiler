#!/usr/bin/env bash
# Поиск в ширину: соседи вершины — строка в массиве, очередь — массив с указателем головы.
graph=("1 2" "0 3" "0 4" "1 5" "2 5" "3 4")
dist=(-1 -1 -1 -1 -1 -1)
dist[0]=0
queue=(0)
order=()
head=0
while ((head < ${#queue[@]})); do
    v=${queue[head++]}
    order+=("$v")
    for u in ${graph[v]}; do
        if ((dist[u] == -1)); then
            dist[u]=$((dist[v] + 1))
            queue+=("$u")
        fi
    done
done
echo "BFS order: ${order[*]}"
echo "Distances: ${dist[*]}"
