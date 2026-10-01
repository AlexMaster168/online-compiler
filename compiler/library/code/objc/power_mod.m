// Быстрое возведение в степень: O(log n).
#import <Foundation/Foundation.h>

static const long long MOD = 1000000007LL;

static long long powerMod(long long base, long long exp, long long m) {
    long long result = 1;
    base %= m;
    while (exp > 0) {
        if (exp & 1) result = result * base % m;
        base = base * base % m;
        exp >>= 1;
    }
    return result;
}

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    printf("2^30 mod %lld = %lld\n", MOD, powerMod(2, 30, MOD));
    printf("3^200 mod %lld = %lld\n", MOD, powerMod(3, 200, MOD));
    [pool drain];
    return 0;
}
