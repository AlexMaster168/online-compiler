// Поиск в ширину: Queue<T>, O(V + E).
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        int[][] graph = { new[] { 1, 2 }, new[] { 0, 3 }, new[] { 0, 4 }, new[] { 1, 5 }, new[] { 2, 5 }, new[] { 3, 4 } };
        var dist = new int[graph.Length];
        Array.Fill(dist, -1);
        var order = new List<int>();
        var queue = new Queue<int>();
        dist[0] = 0;
        queue.Enqueue(0);
        while (queue.Count > 0)
        {
            int v = queue.Dequeue();
            order.Add(v);
            foreach (int u in graph[v])
            {
                if (dist[u] != -1) continue;
                dist[u] = dist[v] + 1;
                queue.Enqueue(u);
            }
        }
        Console.WriteLine("BFS order: " + string.Join(" ", order));
        Console.WriteLine("Distances: " + string.Join(" ", dist));
    }
}
