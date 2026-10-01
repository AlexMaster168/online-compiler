// Поиск в глубину рекурсией: O(V + E). Соседей обходим по возрастанию.
const graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];

function dfs(v, visited = new Set(), order = []) {
  visited.add(v);
  order.push(v);
  for (const u of graph[v]) {
    if (!visited.has(u)) dfs(u, visited, order);
  }
  return order;
}

console.log("DFS order: " + dfs(0).join(" "));
