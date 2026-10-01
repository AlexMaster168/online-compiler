// Сортировка слиянием: subarrayWithRange даёт половины, результат собираем в новый массив.
#import <Foundation/Foundation.h>

static NSArray *mergeSort(NSArray *a) {
    NSUInteger n = [a count];
    if (n <= 1) return a;
    NSArray *left = mergeSort([a subarrayWithRange:NSMakeRange(0, n / 2)]);
    NSArray *right = mergeSort([a subarrayWithRange:NSMakeRange(n / 2, n - n / 2)]);
    NSMutableArray *merged = [NSMutableArray arrayWithCapacity:n];
    NSUInteger i = 0, j = 0;
    while (i < [left count] && j < [right count]) {
        if ([[left objectAtIndex:i] intValue] <= [[right objectAtIndex:j] intValue])
            [merged addObject:[left objectAtIndex:i++]];
        else
            [merged addObject:[right objectAtIndex:j++]];
    }
    while (i < [left count]) [merged addObject:[left objectAtIndex:i++]];
    while (j < [right count]) [merged addObject:[right objectAtIndex:j++]];
    return merged;
}

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    int values[] = {38, 27, 43, 3, 9, 82, 10};
    NSMutableArray *a = [NSMutableArray array];
    for (int i = 0; i < 7; i++) [a addObject:[NSNumber numberWithInt:values[i]]];
    printf("Sorted: %s\n", [[mergeSort(a) componentsJoinedByString:@" "] UTF8String]);
    [pool drain];
    return 0;
}
