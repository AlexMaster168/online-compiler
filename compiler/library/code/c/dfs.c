// Поиск в глубину рекурсией: O(V + E).
#include <stdbool.h>
#include <stdio.h>

#define V 6
static const int adj[V][2] = {{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};
static bool visited[V];

void dfs(int v) {
    visited[v] = true;
    printf(" %d", v);
    for (int k = 0; k < 2; k++)
        if (!visited[adj[v][k]]) dfs(adj[v][k]);
}

int main(void) {
    printf("DFS order:");
    dfs(0);
    printf("\n");
    return 0;
}
