// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
int lcs(String a, String b) {
    int[][] dp = new int[a.size() + 1][b.size() + 1]
    for (i in 1..a.size()) {
        for (j in 1..b.size()) {
            dp[i][j] = a[i - 1] == b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1])
        }
    }
    dp[a.size()][b.size()]
}

println "LCS(ABCBDAB, BDCABA) = ${lcs('ABCBDAB', 'BDCABA')}"
