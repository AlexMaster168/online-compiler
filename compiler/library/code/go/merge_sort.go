// Сортировка слиянием: всегда O(n log n), стабильная.
package main

import (
	"fmt"
	"strings"
)

func mergeSort(a []int) []int {
	if len(a) <= 1 {
		return a
	}
	mid := len(a) / 2
	left, right := mergeSort(a[:mid]), mergeSort(a[mid:])
	merged := make([]int, 0, len(a))
	i, j := 0, 0
	for i < len(left) && j < len(right) {
		if left[i] <= right[j] {
			merged = append(merged, left[i])
			i++
		} else {
			merged = append(merged, right[j])
			j++
		}
	}
	merged = append(merged, left[i:]...)
	return append(merged, right[j:]...)
}

func main() {
	sorted := mergeSort([]int{38, 27, 43, 3, 9, 82, 10})
	fmt.Println("Sorted:", strings.Trim(fmt.Sprint(sorted), "[]"))
}
