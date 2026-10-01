// Решето Эратосфена: O(n log log n).
package main

import (
	"fmt"
	"strings"
)

func sieve(n int) []int {
	composite := make([]bool, n+1)
	var primes []int
	for p := 2; p <= n; p++ {
		if composite[p] {
			continue
		}
		primes = append(primes, p)
		for k := p * p; k <= n; k += p {
			composite[k] = true
		}
	}
	return primes
}

func main() {
	fmt.Println("Primes up to 50:", strings.Trim(fmt.Sprint(sieve(50)), "[]"))
}
