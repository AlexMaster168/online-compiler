// Поиск в глубину вложенной рекурсивной функцией: она видит переменные main.
import std.stdio;

void main()
{
    immutable int[][] graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];
    auto visited = new bool[graph.length];
    int[] order;

    void dfs(int v)
    {
        visited[v] = true;
        order ~= v;
        foreach (u; graph[v])
            if (!visited[u])
                dfs(u);
    }

    dfs(0);
    writefln("DFS order: %(%s %)", order);
}
