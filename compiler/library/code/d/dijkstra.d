// Дейкстра с BinaryHeap: по умолчанию куча максимальная, предикат "a > b" делает её минимальной.
import std.container : BinaryHeap;
import std.stdio;
import std.typecons : Tuple, tuple;

void main()
{
    alias Edge = Tuple!(int, "to", int, "w");
    Edge[][] graph = [[Edge(1, 4), Edge(2, 1)], [Edge(3, 1)], [Edge(1, 2), Edge(3, 5)], [Edge(4, 3)], []];
    auto dist = new int[graph.length];
    dist[] = int.max;
    dist[0] = 0;
    alias Item = Tuple!(int, int);  // (расстояние, вершина)
    Item[] storage;
    auto heap = BinaryHeap!(Item[], "a > b")(storage);
    heap.insert(tuple(0, 0));
    while (!heap.empty)
    {
        auto top = heap.front;
        heap.removeFront();
        immutable d = top[0], v = top[1];
        if (d > dist[v])
            continue; // устаревшая запись
        foreach (e; graph[v])
        {
            if (d + e.w < dist[e.to])
            {
                dist[e.to] = d + e.w;
                heap.insert(tuple(dist[e.to], e.to));
            }
        }
    }
    writefln("Dijkstra from 0: %(%s %)", dist);
}
