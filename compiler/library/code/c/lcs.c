// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
#include <stdio.h>
#include <string.h>

int lcs(const char *a, const char *b) {
    int n = (int)strlen(a), m = (int)strlen(b);
    int dp[n + 1][m + 1];
    for (int i = 0; i <= n; i++)
        for (int j = 0; j <= m; j++) {
            if (i == 0 || j == 0) dp[i][j] = 0;
            else if (a[i - 1] == b[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
            else dp[i][j] = dp[i - 1][j] > dp[i][j - 1] ? dp[i - 1][j] : dp[i][j - 1];
        }
    return dp[n][m];
}

int main(void) {
    printf("LCS(ABCBDAB, BDCABA) = %d\n", lcs("ABCBDAB", "BDCABA"));
    return 0;
}
