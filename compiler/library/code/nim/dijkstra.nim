# Дейкстра с HeapQueue из std/heapqueue: минимальная куча пар (расстояние, вершина).
import std/[heapqueue, strutils]

const graph = [@[(1, 4), (2, 1)], @[(3, 1)], @[(1, 2), (3, 5)], @[(4, 3)], @[]]

var dist = newSeq[int](graph.len)
for d in dist.mitems: d = int.high
dist[0] = 0
var heap = [(0, 0)].toHeapQueue
while heap.len > 0:
  let (d, v) = heap.pop
  if d > dist[v]: continue  # устаревшая запись
  for (u, w) in graph[v]:
    if d + w < dist[u]:
      dist[u] = d + w
      heap.push (dist[u], u)

echo "Dijkstra from 0: ", dist.join(" ")
