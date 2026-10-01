// Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
package main

import "fmt"

func lcs(a, b string) int {
	dp := make([][]int, len(a)+1)
	for i := range dp {
		dp[i] = make([]int, len(b)+1)
	}
	for i := 1; i <= len(a); i++ {
		for j := 1; j <= len(b); j++ {
			if a[i-1] == b[j-1] {
				dp[i][j] = dp[i-1][j-1] + 1
			} else {
				dp[i][j] = max(dp[i-1][j], dp[i][j-1])
			}
		}
	}
	return dp[len(a)][len(b)]
}

func main() {
	fmt.Printf("LCS(ABCBDAB, BDCABA) = %d\n", lcs("ABCBDAB", "BDCABA"))
}
