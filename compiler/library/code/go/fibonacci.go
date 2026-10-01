// Числа Фибоначчи итеративно, O(n). Замыкание-генератор отдаёт числа по одному.
package main

import "fmt"

func fibGenerator() func() int64 {
	a, b := int64(0), int64(1)
	return func() int64 {
		r := a
		a, b = b, a+b
		return r
	}
}

func main() {
	next := fibGenerator()
	fmt.Print("Fibonacci:")
	var f int64
	for i := 0; i <= 50; i++ {
		f = next()
		if i < 15 {
			fmt.Print(" ", f)
		}
	}
	fmt.Printf("\nF(50) = %d\n", f)
}
