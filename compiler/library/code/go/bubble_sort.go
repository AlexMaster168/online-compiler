// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
package main

import (
	"fmt"
	"strings"
)

func bubbleSort(a []int) {
	for i := 0; i < len(a)-1; i++ {
		swapped := false
		for j := 0; j < len(a)-1-i; j++ {
			if a[j] > a[j+1] {
				a[j], a[j+1] = a[j+1], a[j]
				swapped = true
			}
		}
		if !swapped {
			break
		}
	}
}

func join(a []int) string {
	return strings.Trim(fmt.Sprint(a), "[]")
}

func main() {
	a := []int{5, 2, 9, 1, 5, 6}
	bubbleSort(a)
	fmt.Println("Sorted:", join(a))
}
