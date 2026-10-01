// Поиск в ширину: очередь на срезе, O(V + E).
package main

import (
	"fmt"
	"strings"
)

var graph = [][]int{{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}}

func main() {
	dist := make([]int, len(graph))
	for i := range dist {
		dist[i] = -1
	}
	dist[0] = 0
	queue := []int{0}
	var order []int
	for len(queue) > 0 {
		v := queue[0]
		queue = queue[1:]
		order = append(order, v)
		for _, u := range graph[v] {
			if dist[u] == -1 {
				dist[u] = dist[v] + 1
				queue = append(queue, u)
			}
		}
	}
	fmt.Println("BFS order:", strings.Trim(fmt.Sprint(order), "[]"))
	fmt.Println("Distances:", strings.Trim(fmt.Sprint(dist), "[]"))
}
