// Поиск в ширину: очередь на массиве, O(V + E).
#include <stdio.h>

#define V 6
static const int adj[V][2] = {{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};

int main(void) {
    int dist[V], queue[V], head = 0, tail = 0;
    for (int i = 0; i < V; i++) dist[i] = -1;
    dist[0] = 0;
    queue[tail++] = 0;
    printf("BFS order:");
    while (head < tail) {
        int v = queue[head++];
        printf(" %d", v);
        for (int k = 0; k < 2; k++) {
            int u = adj[v][k];
            if (dist[u] == -1) {
                dist[u] = dist[v] + 1;
                queue[tail++] = u;
            }
        }
    }
    printf("\nDistances:");
    for (int i = 0; i < V; i++) printf(" %d", dist[i]);
    printf("\n");
    return 0;
}
