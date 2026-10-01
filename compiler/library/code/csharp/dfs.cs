// Поиск в глубину рекурсией: O(V + E).
using System;
using System.Collections.Generic;

class Program
{
    static readonly int[][] Graph = { new[] { 1, 2 }, new[] { 0, 3 }, new[] { 0, 4 }, new[] { 1, 5 }, new[] { 2, 5 }, new[] { 3, 4 } };

    static void Dfs(int v, bool[] visited, List<int> order)
    {
        visited[v] = true;
        order.Add(v);
        foreach (int u in Graph[v])
            if (!visited[u]) Dfs(u, visited, order);
    }

    static void Main()
    {
        var order = new List<int>();
        Dfs(0, new bool[Graph.Length], order);
        Console.WriteLine("DFS order: " + string.Join(" ", order));
    }
}
