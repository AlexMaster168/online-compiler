// Дейкстра за O(V^2): каждый раз берём ближайшую непосещённую вершину.
const edges = [
  [(1, 4), (2, 1)],
  [(3, 1)],
  [(1, 2), (3, 5)],
  [(4, 3)],
  <(int, int)>[],
];

void main() {
  const inf = 1 << 62;
  final dist = List.filled(edges.length, inf)..[0] = 0;
  final done = List.filled(edges.length, false);
  for (var step = 0; step < edges.length; step++) {
    var v = -1;
    for (var i = 0; i < edges.length; i++) {
      if (!done[i] && (v == -1 || dist[i] < dist[v])) v = i;
    }
    if (dist[v] == inf) break;
    done[v] = true;
    for (final (u, w) in edges[v]) {
      if (dist[v] + w < dist[u]) dist[u] = dist[v] + w;
    }
  }
  print('Dijkstra from 0: ${dist.join(' ')}');
}
