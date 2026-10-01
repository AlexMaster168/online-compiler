// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
package main

import "fmt"

func gcd(a, b int) int {
	for b != 0 {
		a, b = b, a%b
	}
	return a
}

func lcm(a, b int) int { return a / gcd(a, b) * b }

func main() {
	fmt.Printf("GCD(48, 18) = %d\n", gcd(48, 18))
	fmt.Printf("LCM(48, 18) = %d\n", lcm(48, 18))
}
