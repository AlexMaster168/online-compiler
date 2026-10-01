// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
#include <stdio.h>

long long gcd(long long a, long long b) {
    while (b != 0) {
        long long t = a % b;
        a = b;
        b = t;
    }
    return a;
}

long long lcm(long long a, long long b) { return a / gcd(a, b) * b; }

int main(void) {
    printf("GCD(48, 18) = %lld\n", gcd(48, 18));
    printf("LCM(48, 18) = %lld\n", lcm(48, 18));
    return 0;
}
