// Наибольшая общая подпоследовательность: символы берём методом characterAtIndex: у NSString.
#import <Foundation/Foundation.h>

static NSUInteger lcs(NSString *a, NSString *b) {
    NSUInteger n = [a length], m = [b length];
    NSUInteger dp[n + 1][m + 1];
    for (NSUInteger i = 0; i <= n; i++)
        for (NSUInteger j = 0; j <= m; j++) {
            if (i == 0 || j == 0) dp[i][j] = 0;
            else if ([a characterAtIndex:i - 1] == [b characterAtIndex:j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
            else dp[i][j] = MAX(dp[i - 1][j], dp[i][j - 1]);
        }
    return dp[n][m];
}

int main(void) {
    NSAutoreleasePool *pool = [[NSAutoreleasePool alloc] init];
    printf("LCS(ABCBDAB, BDCABA) = %lu\n", (unsigned long)lcs(@"ABCBDAB", @"BDCABA"));
    [pool drain];
    return 0;
}
