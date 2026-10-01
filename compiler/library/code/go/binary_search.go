// Бинарный поиск: O(log n). (В пакете sort есть sort.SearchInts — здесь пишем руками.)
package main

import "fmt"

func binarySearch(a []int, target int) int {
	lo, hi := 0, len(a)-1
	for lo <= hi {
		mid := lo + (hi-lo)/2
		switch {
		case a[mid] == target:
			return mid
		case a[mid] < target:
			lo = mid + 1
		default:
			hi = mid - 1
		}
	}
	return -1
}

func main() {
	a := []int{1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
	for _, target := range []int{7, 4} {
		if i := binarySearch(a, target); i >= 0 {
			fmt.Printf("Found %d at index %d\n", target, i)
		} else {
			fmt.Printf("%d not found\n", target)
		}
	}
}
