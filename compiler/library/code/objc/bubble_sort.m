// Сортировка пузырьком на NSMutableArray из NSNumber.
// Это GCC + GNUstep: литералов @5, @[...] и индексации a[i] (расширения clang) здесь нет —
// используем классические методы numberWithInt: и objectAtIndex:.
#import <Foundation/Foundation.h>

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    int values[] = {5, 2, 9, 1, 5, 6};
    NSMutableArray *a = [NSMutableArray array];
    for (int i = 0; i < 6; i++) [a addObject:[NSNumber numberWithInt:values[i]]];

    NSUInteger n = [a count];
    for (NSUInteger i = 0; i + 1 < n; i++) {
        BOOL swapped = NO;
        for (NSUInteger j = 0; j + 1 < n - i; j++) {
            if ([[a objectAtIndex:j] compare:[a objectAtIndex:j + 1]] == NSOrderedDescending) {
                [a exchangeObjectAtIndex:j withObjectAtIndex:j + 1];
                swapped = YES;
            }
        }
        if (!swapped) break;
    }
    printf("Sorted: %s\n", [[a componentsJoinedByString:@" "] UTF8String]);
    [pool drain];
    return 0;
}
