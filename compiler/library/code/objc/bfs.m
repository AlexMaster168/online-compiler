// Поиск в ширину: очередь — NSMutableArray из NSNumber, соседи — C-массив.
#import <Foundation/Foundation.h>

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    const int graph[6][2] = {{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};
    int dist[6] = {0, -1, -1, -1, -1, -1};
    NSMutableArray *queue = [NSMutableArray arrayWithObject:[NSNumber numberWithInt:0]];
    NSMutableArray *order = [NSMutableArray array];
    while ([queue count] > 0) {
        int v = [[queue objectAtIndex:0] intValue];
        [queue removeObjectAtIndex:0];
        [order addObject:[NSNumber numberWithInt:v]];
        for (int k = 0; k < 2; k++) {
            int u = graph[v][k];
            if (dist[u] == -1) {
                dist[u] = dist[v] + 1;
                [queue addObject:[NSNumber numberWithInt:u]];
            }
        }
    }
    printf("BFS order: %s\n", [[order componentsJoinedByString:@" "] UTF8String]);
    printf("Distances:");
    for (int i = 0; i < 6; i++) printf(" %d", dist[i]);
    printf("\n");
    [pool drain];
    return 0;
}
