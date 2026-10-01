// Поиск в глубину рекурсивной лямбдой (C++23 deducing this не нужен — std::function хватает).
#include <functional>
#include <iostream>
#include <vector>

int main() {
    const std::vector<std::vector<int>> graph{{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};
    std::vector<bool> visited(graph.size());
    std::function<void(int)> dfs = [&](int v) {
        visited[v] = true;
        std::cout << ' ' << v;
        for (int u : graph[v])
            if (!visited[u]) dfs(u);
    };
    std::cout << "DFS order:";
    dfs(0);
    std::cout << '\n';
}
