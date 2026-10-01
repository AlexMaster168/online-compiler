// Поиск в ширину: Queue из dart:collection, O(V + E).
import 'dart:collection';

const graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];

void main() {
  final dist = List.filled(graph.length, -1);
  final order = <int>[];
  final queue = Queue<int>()..add(0);
  dist[0] = 0;
  while (queue.isNotEmpty) {
    final v = queue.removeFirst();
    order.add(v);
    for (final u in graph[v]) {
      if (dist[u] == -1) {
        dist[u] = dist[v] + 1;
        queue.add(u);
      }
    }
  }
  print('BFS order: ${order.join(' ')}');
  print('Distances: ${dist.join(' ')}');
}
