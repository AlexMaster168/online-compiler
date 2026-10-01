// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
function lcs(a, b) {
  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[a.length][b.length];
}

console.log(`LCS(ABCBDAB, BDCABA) = ${lcs("ABCBDAB", "BDCABA")}`);
