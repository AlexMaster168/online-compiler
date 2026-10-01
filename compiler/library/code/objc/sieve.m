// Решето Эратосфена: вычеркнутые числа храним в NSMutableIndexSet — множестве индексов.
#import <Foundation/Foundation.h>

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    const NSUInteger n = 50;
    NSMutableIndexSet *composite = [NSMutableIndexSet indexSet];
    printf("Primes up to %lu:", (unsigned long)n);
    for (NSUInteger p = 2; p <= n; p++) {
        if ([composite containsIndex:p]) continue;
        printf(" %lu", (unsigned long)p);
        for (NSUInteger k = p * p; k <= n; k += p) [composite addIndex:k];
    }
    printf("\n");
    [pool drain];
    return 0;
}
