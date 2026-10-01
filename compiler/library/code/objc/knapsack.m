// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
#import <Foundation/Foundation.h>

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    const int weights[] = {1, 3, 4, 5}, values[] = {1, 4, 5, 7};
    const int capacity = 7;
    int dp[8] = {0};
    for (int i = 0; i < 4; i++)
        for (int c = capacity; c >= weights[i]; c--) dp[c] = MAX(dp[c], dp[c - weights[i]] + values[i]);
    printf("Knapsack max value: %d\n", dp[capacity]);
    [pool drain];
    return 0;
}
