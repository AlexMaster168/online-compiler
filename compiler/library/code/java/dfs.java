// Поиск в глубину рекурсией: O(V + E).
import java.util.StringJoiner;

public class Main {
    static final int[][] GRAPH = {{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};
    static final boolean[] visited = new boolean[GRAPH.length];
    static final StringJoiner order = new StringJoiner(" ");

    static void dfs(int v) {
        visited[v] = true;
        order.add(String.valueOf(v));
        for (int u : GRAPH[v]) {
            if (!visited[u]) dfs(u);
        }
    }

    public static void main(String[] args) {
        dfs(0);
        System.out.println("DFS order: " + order);
    }
}
