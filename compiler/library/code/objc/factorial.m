// Факториал рекурсией. unsigned long long — 64 бита, 20! помещается.
#import <Foundation/Foundation.h>

static unsigned long long factorial(unsigned int n) {
    return n <= 1 ? 1ULL : n * factorial(n - 1);
}

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    printf("10! = %llu\n", factorial(10));
    printf("20! = %llu\n", factorial(20));
    [pool drain];
    return 0;
}
