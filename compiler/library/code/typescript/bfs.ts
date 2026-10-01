// Поиск в ширину: очередь, O(V + E).
const graph: number[][] = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];

function bfs(start: number): { order: number[]; dist: number[] } {
  const dist = new Array<number>(graph.length).fill(-1);
  const order: number[] = [];
  const queue = [start];
  dist[start] = 0;
  for (let head = 0; head < queue.length; head++) {
    const v = queue[head];
    order.push(v);
    for (const u of graph[v]) {
      if (dist[u] === -1) {
        dist[u] = dist[v] + 1;
        queue.push(u);
      }
    }
  }
  return { order, dist };
}

const { order, dist } = bfs(0);
console.log("BFS order: " + order.join(" "));
console.log("Distances: " + dist.join(" "));
