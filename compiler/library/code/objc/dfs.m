// Поиск в глубину рекурсией: класс Graph хранит соседей, посещённые вершины и порядок обхода.
#import <Foundation/Foundation.h>

@interface Graph : NSObject {
    BOOL visited[6];
    NSMutableArray *order;
}
- (NSArray *)dfsFrom:(int)start;
@end

static const int adjacency[6][2] = {{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}};

@implementation Graph
- (id)init {
    if ((self = [super init])) order = [[NSMutableArray alloc] init];
    return self;
}

- (void)dealloc {
    [order release];  // ручное управление памятью: без ARC память освобождаем сами
    [super dealloc];
}

- (void)visit:(int)v {
    visited[v] = YES;
    [order addObject:[NSNumber numberWithInt:v]];
    for (int k = 0; k < 2; k++) {
        int u = adjacency[v][k];
        if (!visited[u]) [self visit:u];
    }
}

- (NSArray *)dfsFrom:(int)start {
    [self visit:start];
    return order;
}
@end

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    Graph *g = [[Graph alloc] init];
    printf("DFS order: %s\n", [[[g dfsFrom:0] componentsJoinedByString:@" "] UTF8String]);
    [g release];
    [pool drain];
    return 0;
}
