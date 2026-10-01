// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
func lcs(_ s: String, _ t: String) -> Int {
    let a = Array(s), b = Array(t)
    var dp = [[Int]](repeating: [Int](repeating: 0, count: b.count + 1), count: a.count + 1)
    for i in 1...a.count {
        for j in 1...b.count {
            dp[i][j] = a[i - 1] == b[j - 1] ? dp[i - 1][j - 1] + 1 : max(dp[i - 1][j], dp[i][j - 1])
        }
    }
    return dp[a.count][b.count]
}

print("LCS(ABCBDAB, BDCABA) = \(lcs("ABCBDAB", "BDCABA"))")
