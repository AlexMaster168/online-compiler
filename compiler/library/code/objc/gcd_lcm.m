// НОД по Евклиду как метод класса — так в Objective-C оформляют «статические» функции.
#import <Foundation/Foundation.h>

@interface MathUtils : NSObject
+ (long)gcd:(long)a with:(long)b;
+ (long)lcm:(long)a with:(long)b;
@end

@implementation MathUtils
+ (long)gcd:(long)a with:(long)b {
    return b == 0 ? a : [self gcd:b with:a % b];
}
+ (long)lcm:(long)a with:(long)b {
    return a / [self gcd:a with:b] * b;
}
@end

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    printf("GCD(48, 18) = %ld\n", [MathUtils gcd:48 with:18]);
    printf("LCM(48, 18) = %ld\n", [MathUtils lcm:48 with:18]);
    [pool drain];
    return 0;
}
