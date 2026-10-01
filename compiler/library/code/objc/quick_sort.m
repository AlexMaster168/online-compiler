// Быстрая сортировка (разбиение Ломуто) как категория NSMutableArray: метод добавляется в чужой класс.
#import <Foundation/Foundation.h>

@interface NSMutableArray (QuickSort)
- (void)quickSortFrom:(NSInteger)lo to:(NSInteger)hi;
@end

@implementation NSMutableArray (QuickSort)
- (void)quickSortFrom:(NSInteger)lo to:(NSInteger)hi {
    if (lo >= hi) return;
    int pivot = [[self objectAtIndex:hi] intValue];
    NSInteger i = lo;
    for (NSInteger j = lo; j < hi; j++) {
        if ([[self objectAtIndex:j] intValue] < pivot) {
            [self exchangeObjectAtIndex:i withObjectAtIndex:j];
            i++;
        }
    }
    [self exchangeObjectAtIndex:i withObjectAtIndex:hi];
    [self quickSortFrom:lo to:i - 1];
    [self quickSortFrom:i + 1 to:hi];
}
@end

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    int values[] = {10, 7, 8, 9, 1, 5, 3};
    NSMutableArray *a = [NSMutableArray array];
    for (int i = 0; i < 7; i++) [a addObject:[NSNumber numberWithInt:values[i]]];
    [a quickSortFrom:0 to:(NSInteger)[a count] - 1];
    printf("Sorted: %s\n", [[a componentsJoinedByString:@" "] UTF8String]);
    [pool drain];
    return 0;
}
