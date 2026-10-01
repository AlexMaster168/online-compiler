// Быстрая сортировка (разбиение Ломуто): в среднем O(n log n), в худшем O(n^2).
package main

import (
	"fmt"
	"strings"
)

func partition(a []int) int {
	hi := len(a) - 1
	pivot, i := a[hi], 0
	for j := 0; j < hi; j++ {
		if a[j] < pivot {
			a[i], a[j] = a[j], a[i]
			i++
		}
	}
	a[i], a[hi] = a[hi], a[i]
	return i
}

// Работаем со срезами: они смотрят в тот же массив, копий нет
func quickSort(a []int) {
	if len(a) < 2 {
		return
	}
	p := partition(a)
	quickSort(a[:p])
	quickSort(a[p+1:])
}

func main() {
	a := []int{10, 7, 8, 9, 1, 5, 3}
	quickSort(a)
	fmt.Println("Sorted:", strings.Trim(fmt.Sprint(a), "[]"))
}
