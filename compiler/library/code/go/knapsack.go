// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
package main

import "fmt"

func knapsack(weights, values []int, capacity int) int {
	dp := make([]int, capacity+1)
	for i, w := range weights {
		for c := capacity; c >= w; c-- {
			dp[c] = max(dp[c], dp[c-w]+values[i])
		}
	}
	return dp[capacity]
}

func main() {
	fmt.Println("Knapsack max value:", knapsack([]int{1, 3, 4, 5}, []int{1, 4, 5, 7}, 7))
}
