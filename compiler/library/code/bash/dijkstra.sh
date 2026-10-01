#!/usr/bin/env bash
# Дейкстра за O(V^2) на матрице весов (0 — нет ребра), матрица развёрнута в одномерный массив.
n=5
w=(
    0 4 1 0 0
    0 0 0 1 0
    0 2 0 5 0
    0 0 0 0 3
    0 0 0 0 0
)
INF=1000000000
dist=() done_=()  # done — ключевое слово bash, поэтому done_
for ((i = 0; i < n; i++)); do dist[i]=$INF; done_[i]=0; done
dist[0]=0
for ((step = 0; step < n; step++)); do
    v=-1
    for ((i = 0; i < n; i++)); do
        if ((!done_[i] && (v == -1 || dist[i] < dist[v]))); then v=$i; fi
    done
    ((dist[v] == INF)) && break
    done_[v]=1
    for ((u = 0; u < n; u++)); do
        wt=${w[v * n + u]}
        if ((wt && dist[v] + wt < dist[u])); then dist[u]=$((dist[v] + wt)); fi
    done
done
echo "Dijkstra from 0: ${dist[*]}"
