// Числа Фибоначчи итеративно; строки собираем в NSMutableArray и склеиваем componentsJoinedByString.
#import <Foundation/Foundation.h>

static long long fib(int n) {
    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        long long t = a + b;
        a = b;
        b = t;
    }
    return a;
}

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    NSMutableArray *first = [NSMutableArray array];
    for (int i = 0; i < 15; i++) [first addObject:[NSString stringWithFormat:@"%lld", fib(i)]];
    printf("Fibonacci: %s\n", [[first componentsJoinedByString:@" "] UTF8String]);
    printf("F(50) = %lld\n", fib(50));
    [pool drain];
    return 0;
}
