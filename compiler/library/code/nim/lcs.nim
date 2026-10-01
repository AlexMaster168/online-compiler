# Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
proc lcs(a, b: string): int =
  var dp = newSeq[seq[int]](a.len + 1)
  for row in dp.mitems: row = newSeq[int](b.len + 1)
  for i in 1 .. a.len:
    for j in 1 .. b.len:
      dp[i][j] = if a[i - 1] == b[j - 1]: dp[i - 1][j - 1] + 1 else: max(dp[i - 1][j], dp[i][j - 1])
  dp[a.len][b.len]

echo "LCS(ABCBDAB, BDCABA) = ", lcs("ABCBDAB", "BDCABA")
