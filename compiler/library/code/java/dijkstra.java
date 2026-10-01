// Дейкстра с PriorityQueue: O((V + E) log V).
import java.util.Arrays;
import java.util.List;
import java.util.PriorityQueue;
import java.util.StringJoiner;

public class Main {
    record Edge(int to, int weight) {}

    public static void main(String[] args) {
        List<List<Edge>> graph = List.of(
                List.of(new Edge(1, 4), new Edge(2, 1)),
                List.of(new Edge(3, 1)),
                List.of(new Edge(1, 2), new Edge(3, 5)),
                List.of(new Edge(4, 3)),
                List.of());
        int[] dist = new int[graph.size()];
        Arrays.fill(dist, Integer.MAX_VALUE);
        dist[0] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>((x, y) -> Integer.compare(x[0], y[0]));
        pq.add(new int[] {0, 0});
        while (!pq.isEmpty()) {
            int[] top = pq.poll();
            int d = top[0], v = top[1];
            if (d > dist[v]) continue;  // устаревшая запись
            for (Edge e : graph.get(v)) {
                if (d + e.weight() < dist[e.to()]) {
                    dist[e.to()] = d + e.weight();
                    pq.add(new int[] {dist[e.to()], e.to()});
                }
            }
        }
        StringJoiner out = new StringJoiner(" ");
        for (int d : dist) out.add(String.valueOf(d));
        System.out.println("Dijkstra from 0: " + out);
    }
}
