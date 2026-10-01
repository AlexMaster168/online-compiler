// Поиск в ширину: std.container.DList как очередь, O(V + E).
import std.container : DList;
import std.stdio;

void main()
{
    immutable int[][] graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];
    auto dist = new int[graph.length];
    dist[] = -1;  // присваивание всем элементам среза
    int[] order;
    auto queue = DList!int(0);
    dist[0] = 0;
    while (!queue.empty)
    {
        immutable v = queue.front;
        queue.removeFront();
        order ~= v;
        foreach (int u; graph[v])  // int, а не immutable(int): иначе DList не сможет сделать копию узла
        {
            if (dist[u] == -1)
            {
                dist[u] = dist[v] + 1;
                queue.insertBack(u);
            }
        }
    }
    writefln("BFS order: %(%s %)", order);
    writefln("Distances: %(%s %)", dist);
}
