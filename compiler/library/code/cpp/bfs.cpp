// Поиск в ширину: std::queue, O(V + E).
#include <iostream>
#include <queue>
#include <vector>

int main() {
    const std::vector<std::vector<int>> graph{{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};
    std::vector<int> dist(graph.size(), -1);
    std::queue<int> q;
    dist[0] = 0;
    q.push(0);
    std::cout << "BFS order:";
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        std::cout << ' ' << v;
        for (int u : graph[v]) {
            if (dist[u] == -1) {
                dist[u] = dist[v] + 1;
                q.push(u);
            }
        }
    }
    std::cout << "\nDistances:";
    for (int d : dist) std::cout << ' ' << d;
    std::cout << '\n';
}
