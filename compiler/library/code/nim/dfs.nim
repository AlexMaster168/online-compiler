# Поиск в глубину рекурсией: HashSet посещённых из std/sets.
import std/[sets, strutils]

const graph = [@[1, 2], @[0, 3], @[0, 4], @[1, 5], @[2, 5], @[3, 4]]

proc dfs(v: int, visited: var HashSet[int], order: var seq[int]) =
  visited.incl v
  order.add v
  for u in graph[v]:
    if u notin visited: dfs(u, visited, order)

var visited: HashSet[int]
var order: seq[int]
dfs(0, visited, order)
echo "DFS order: ", order.join(" ")
