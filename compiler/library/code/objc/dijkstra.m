// Дейкстра за O(V^2) на C-массивах: Objective-C — надмножество C, и для чисел это проще всего.
#import <Foundation/Foundation.h>
#include <limits.h>

#define V 5

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    const int w[V][V] = {
        {0, 4, 1, 0, 0},
        {0, 0, 0, 1, 0},
        {0, 2, 0, 5, 0},
        {0, 0, 0, 0, 3},
        {0, 0, 0, 0, 0},
    };
    int dist[V];
    BOOL done[V] = {NO};
    for (int i = 0; i < V; i++) dist[i] = INT_MAX;
    dist[0] = 0;
    for (int step = 0; step < V; step++) {
        int v = -1;
        for (int i = 0; i < V; i++)
            if (!done[i] && (v == -1 || dist[i] < dist[v])) v = i;
        if (dist[v] == INT_MAX) break;
        done[v] = YES;
        for (int u = 0; u < V; u++)
            if (w[v][u] && dist[v] + w[v][u] < dist[u]) dist[u] = dist[v] + w[v][u];
    }
    printf("Dijkstra from 0:");
    for (int i = 0; i < V; i++) printf(" %d", dist[i]);
    printf("\n");
    [pool drain];
    return 0;
}
