// Поиск в глубину рекурсией: O(V + E).
const graph: number[][] = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];

function dfs(v: number, visited = new Set<number>(), order: number[] = []): number[] {
  visited.add(v);
  order.push(v);
  for (const u of graph[v]) {
    if (!visited.has(u)) dfs(u, visited, order);
  }
  return order;
}

console.log("DFS order: " + dfs(0).join(" "));
