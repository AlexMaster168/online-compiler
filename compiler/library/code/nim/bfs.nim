# Поиск в ширину: Deque из std/deques — двусторонняя очередь.
import std/[deques, strutils]

const graph = [@[1, 2], @[0, 3], @[0, 4], @[1, 5], @[2, 5], @[3, 4]]

var dist = newSeq[int](graph.len)
for d in dist.mitems: d = -1
var order: seq[int]
var queue = [0].toDeque
dist[0] = 0
while queue.len > 0:
  let v = queue.popFirst
  order.add v
  for u in graph[v]:
    if dist[u] == -1:
      dist[u] = dist[v] + 1
      queue.addLast u

echo "BFS order: ", order.join(" ")
echo "Distances: ", dist.join(" ")
