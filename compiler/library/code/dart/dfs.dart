// Поиск в глубину рекурсией: O(V + E).
const graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];

void dfs(int v, Set<int> visited, List<int> order) {
  visited.add(v);
  order.add(v);
  for (final u in graph[v]) {
    if (!visited.contains(u)) dfs(u, visited, order);
  }
}

void main() {
  final order = <int>[];
  dfs(0, {}, order);
  print('DFS order: ${order.join(' ')}');
}
