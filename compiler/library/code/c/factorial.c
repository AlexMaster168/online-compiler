// Факториал рекурсией. 20! — максимум, что помещается в unsigned long long (64 бита).
#include <stdio.h>

unsigned long long factorial(int n) { return n <= 1 ? 1ULL : (unsigned long long)n * factorial(n - 1); }

int main(void) {
    printf("10! = %llu\n", factorial(10));
    printf("20! = %llu\n", factorial(20));
    return 0;
}
