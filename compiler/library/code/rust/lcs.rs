// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
fn lcs(a: &str, b: &str) -> usize {
    let (a, b) = (a.as_bytes(), b.as_bytes());
    let mut dp = vec![vec![0usize; b.len() + 1]; a.len() + 1];
    for i in 1..=a.len() {
        for j in 1..=b.len() {
            dp[i][j] = if a[i - 1] == b[j - 1] {
                dp[i - 1][j - 1] + 1
            } else {
                dp[i - 1][j].max(dp[i][j - 1])
            };
        }
    }
    dp[a.len()][b.len()]
}

fn main() {
    println!("LCS(ABCBDAB, BDCABA) = {}", lcs("ABCBDAB", "BDCABA"));
}
