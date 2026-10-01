// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
public class Main {
    static int lcs(String a, String b) {
        int[][] dp = new int[a.length() + 1][b.length() + 1];
        for (int i = 1; i <= a.length(); i++) {
            for (int j = 1; j <= b.length(); j++) {
                dp[i][j] = a.charAt(i - 1) == b.charAt(j - 1)
                        ? dp[i - 1][j - 1] + 1
                        : Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        return dp[a.length()][b.length()];
    }

    public static void main(String[] args) {
        System.out.println("LCS(ABCBDAB, BDCABA) = " + lcs("ABCBDAB", "BDCABA"));
    }
}
