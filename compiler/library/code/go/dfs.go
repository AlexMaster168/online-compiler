// Поиск в глубину рекурсией: O(V + E).
package main

import (
	"fmt"
	"strings"
)

var graph = [][]int{{1, 2}, {0, 3}, {0, 4}, {1, 5}, {2, 5}, {3, 4}}

func dfs(v int, visited []bool, order []int) []int {
	visited[v] = true
	order = append(order, v)
	for _, u := range graph[v] {
		if !visited[u] {
			order = dfs(u, visited, order)
		}
	}
	return order
}

func main() {
	order := dfs(0, make([]bool, len(graph)), nil)
	fmt.Println("DFS order:", strings.Trim(fmt.Sprint(order), "[]"))
}
