// Быстрое возведение в степень: O(log n). Оба множителя < 1e9+7, произведение < 2^63 — long long хватает.
#include <stdio.h>

#define MOD 1000000007LL

long long power_mod(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = result * base % mod;
        base = base * base % mod;
        exp >>= 1;
    }
    return result;
}

int main(void) {
    printf("2^30 mod %lld = %lld\n", MOD, power_mod(2, 30, MOD));
    printf("3^200 mod %lld = %lld\n", MOD, power_mod(3, 200, MOD));
    return 0;
}
