// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
#include <stdio.h>

int main(void) {
    int weights[] = {1, 3, 4, 5}, values[] = {1, 4, 5, 7};
    enum { ITEMS = 4, CAPACITY = 7 };
    int dp[CAPACITY + 1] = {0};
    for (int i = 0; i < ITEMS; i++)
        for (int c = CAPACITY; c >= weights[i]; c--)
            if (dp[c - weights[i]] + values[i] > dp[c]) dp[c] = dp[c - weights[i]] + values[i];
    printf("Knapsack max value: %d\n", dp[CAPACITY]);
    return 0;
}
