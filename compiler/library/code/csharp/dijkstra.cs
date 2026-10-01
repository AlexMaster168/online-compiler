// Дейкстра с PriorityQueue (.NET 6+): O((V + E) log V).
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        var graph = new (int To, int W)[][]
        {
            new[] { (1, 4), (2, 1) },
            new[] { (3, 1) },
            new[] { (1, 2), (3, 5) },
            new[] { (4, 3) },
            Array.Empty<(int, int)>(),
        };
        var dist = new int[graph.Length];
        Array.Fill(dist, int.MaxValue);
        dist[0] = 0;
        var pq = new PriorityQueue<int, int>();
        pq.Enqueue(0, 0);
        while (pq.TryDequeue(out int v, out int d))
        {
            if (d > dist[v]) continue;  // устаревшая запись
            foreach (var (to, w) in graph[v])
            {
                if (d + w >= dist[to]) continue;
                dist[to] = d + w;
                pq.Enqueue(to, dist[to]);
            }
        }
        Console.WriteLine("Dijkstra from 0: " + string.Join(" ", dist));
    }
}
