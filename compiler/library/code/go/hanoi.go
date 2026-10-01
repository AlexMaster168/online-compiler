// Ханойские башни: 2^n - 1 ходов.
package main

import "fmt"

func hanoi(n int, source, spare, target string, moves *int) {
	if n == 0 {
		return
	}
	hanoi(n-1, source, target, spare, moves)
	fmt.Printf("Move disk %d from %s to %s\n", n, source, target)
	*moves++
	hanoi(n-1, spare, source, target, moves)
}

func main() {
	moves := 0
	hanoi(3, "A", "B", "C", &moves)
	fmt.Println("Total moves:", moves)
}
