// Дейкстра с приоритетной очередью: O((V + E) log V).
#include <functional>
#include <iostream>
#include <limits>
#include <queue>
#include <utility>
#include <vector>

int main() {
    using Edge = std::pair<int, int>;  // {куда, вес}
    const std::vector<std::vector<Edge>> graph{{{1, 4}, {2, 1}}, {{3, 1}}, {{1, 2}, {3, 5}}, {{4, 3}}, {}};
    std::vector<int> dist(graph.size(), std::numeric_limits<int>::max());
    std::priority_queue<std::pair<int, int>, std::vector<std::pair<int, int>>, std::greater<>> pq;
    dist[0] = 0;
    pq.push({0, 0});
    while (!pq.empty()) {
        auto [d, v] = pq.top();
        pq.pop();
        if (d > dist[v]) continue;  // устаревшая запись
        for (auto [u, w] : graph[v]) {
            if (d + w < dist[u]) {
                dist[u] = d + w;
                pq.push({dist[u], u});
            }
        }
    }
    std::cout << "Dijkstra from 0:";
    for (int d : dist) std::cout << ' ' << d;
    std::cout << '\n';
}
