// Быстрое возведение в степень: O(log n).
package main

import "fmt"

const mod = 1_000_000_007

func powerMod(base, exp, m int64) int64 {
	result := int64(1)
	base %= m
	for exp > 0 {
		if exp&1 == 1 {
			result = result * base % m
		}
		base = base * base % m
		exp >>= 1
	}
	return result
}

func main() {
	fmt.Printf("2^30 mod %d = %d\n", mod, powerMod(2, 30, mod))
	fmt.Printf("3^200 mod %d = %d\n", mod, powerMod(3, 200, mod))
}
