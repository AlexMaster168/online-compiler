// Дейкстра за O(V^2): на каждом шаге берём ближайшую непосещённую вершину.
const edges = [[[1, 4], [2, 1]], [[3, 1]], [[1, 2], [3, 5]], [[4, 3]], []];

function dijkstra(start) {
  const n = edges.length;
  const dist = new Array(n).fill(Infinity);
  const done = new Array(n).fill(false);
  dist[start] = 0;
  for (let step = 0; step < n; step++) {
    let v = -1;
    for (let i = 0; i < n; i++) {
      if (!done[i] && (v === -1 || dist[i] < dist[v])) v = i;
    }
    if (dist[v] === Infinity) break;
    done[v] = true;
    for (const [u, w] of edges[v]) dist[u] = Math.min(dist[u], dist[v] + w);
  }
  return dist;
}

console.log("Dijkstra from 0: " + dijkstra(0).join(" "));
