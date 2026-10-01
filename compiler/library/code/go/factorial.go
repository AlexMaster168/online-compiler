// Факториал рекурсией. 20! — максимум для uint64.
package main

import "fmt"

func factorial(n uint64) uint64 {
	if n <= 1 {
		return 1
	}
	return n * factorial(n-1)
}

func main() {
	fmt.Printf("10! = %d\n", factorial(10))
	fmt.Printf("20! = %d\n", factorial(20))
}
