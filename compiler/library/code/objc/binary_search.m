// Бинарный поиск: NSNotFound — стандартный в Foundation маркер «не нашли».
#import <Foundation/Foundation.h>

static NSUInteger binarySearch(NSArray *a, int target) {
    NSInteger lo = 0, hi = (NSInteger)[a count] - 1;
    while (lo <= hi) {
        NSInteger mid = lo + (hi - lo) / 2;
        int value = [[a objectAtIndex:mid] intValue];
        if (value == target) return (NSUInteger)mid;
        if (value < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return NSNotFound;
}

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    NSMutableArray *arr = [NSMutableArray array];
    for (int v = 1; v <= 19; v += 2) [arr addObject:[NSNumber numberWithInt:v]];
    int targets[] = {7, 4};
    for (int t = 0; t < 2; t++) {
        NSUInteger i = binarySearch(arr, targets[t]);
        if (i != NSNotFound) printf("Found %d at index %lu\n", targets[t], (unsigned long)i);
        else printf("%d not found\n", targets[t]);
    }
    [pool drain];
    return 0;
}
