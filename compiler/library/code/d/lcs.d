// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
import std.algorithm : max;
import std.stdio;

size_t lcs(string a, string b)
{
    auto dp = new size_t[][](a.length + 1, b.length + 1);  // заполнено нулями
    foreach (i; 1 .. a.length + 1)
        foreach (j; 1 .. b.length + 1)
            dp[i][j] = a[i - 1] == b[j - 1] ? dp[i - 1][j - 1] + 1 : max(dp[i - 1][j], dp[i][j - 1]);
    return dp[a.length][b.length];
}

void main()
{
    writefln("LCS(ABCBDAB, BDCABA) = %d", lcs("ABCBDAB", "BDCABA"));
}
