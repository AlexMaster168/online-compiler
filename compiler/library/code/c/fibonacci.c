// Числа Фибоначчи итеративно, O(n). F(50) не влезает в 32 бита — long long.
#include <stdio.h>

long long fib(int n) {
    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        long long t = a + b;
        a = b;
        b = t;
    }
    return a;
}

int main(void) {
    printf("Fibonacci:");
    for (int i = 0; i < 15; i++) printf(" %lld", fib(i));
    printf("\nF(50) = %lld\n", fib(50));
    return 0;
}
