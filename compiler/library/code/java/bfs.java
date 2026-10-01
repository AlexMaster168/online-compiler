// Поиск в ширину: ArrayDeque как очередь, O(V + E).
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.StringJoiner;

public class Main {
    static final int[][] GRAPH = {{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};

    public static void main(String[] args) {
        int[] dist = new int[GRAPH.length];
        Arrays.fill(dist, -1);
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        StringJoiner order = new StringJoiner(" ");
        dist[0] = 0;
        queue.add(0);
        while (!queue.isEmpty()) {
            int v = queue.poll();
            order.add(String.valueOf(v));
            for (int u : GRAPH[v]) {
                if (dist[u] == -1) {
                    dist[u] = dist[v] + 1;
                    queue.add(u);
                }
            }
        }
        StringJoiner distances = new StringJoiner(" ");
        for (int d : dist) distances.add(String.valueOf(d));
        System.out.println("BFS order: " + order);
        System.out.println("Distances: " + distances);
    }
}
