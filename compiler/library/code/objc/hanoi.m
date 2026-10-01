// Ханойские башни: рекурсивный метод объекта; счётчик ходов — переменная экземпляра.
#import <Foundation/Foundation.h>

@interface Towers : NSObject {
    int moves;
}
- (void)move:(int)n from:(char)source via:(char)spare to:(char)target;
- (int)moves;
@end

@implementation Towers
- (void)move:(int)n from:(char)source via:(char)spare to:(char)target {
    if (n == 0) return;
    [self move:n - 1 from:source via:target to:spare];
    printf("Move disk %d from %c to %c\n", n, source, target);
    moves++;
    [self move:n - 1 from:spare via:source to:target];
}
- (int)moves {
    return moves;
}
@end

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    Towers *towers = [[[Towers alloc] init] autorelease];
    [towers move:3 from:'A' via:'B' to:'C'];
    printf("Total moves: %d\n", [towers moves]);
    [pool drain];
    return 0;
}
