// Решето Эратосфена: O(n log log n).
#include <stdbool.h>
#include <stdio.h>

#define N 50

int main(void) {
    bool composite[N + 1] = {false};
    printf("Primes up to %d:", N);
    for (int p = 2; p <= N; p++) {
        if (composite[p]) continue;
        printf(" %d", p);
        for (int k = p * p; k <= N; k += p) composite[k] = true;
    }
    printf("\n");
    return 0;
}
