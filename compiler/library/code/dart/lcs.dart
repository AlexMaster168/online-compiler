// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
import 'dart:math';

int lcs(String a, String b) {
  final dp = List.generate(a.length + 1, (_) => List.filled(b.length + 1, 0));
  for (var i = 1; i <= a.length; i++) {
    for (var j = 1; j <= b.length; j++) {
      dp[i][j] = a[i - 1] == b[j - 1] ? dp[i - 1][j - 1] + 1 : max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[a.length][b.length];
}

void main() {
  print('LCS(ABCBDAB, BDCABA) = ${lcs('ABCBDAB', 'BDCABA')}');
}
