// Дейкстра с кучей из container/heap: O((V + E) log V).
package main

import (
	"container/heap"
	"fmt"
	"math"
	"strings"
)

type edge struct{ to, w int }
type item struct{ dist, v int }
type minHeap []item

func (h minHeap) Len() int            { return len(h) }
func (h minHeap) Less(i, j int) bool  { return h[i].dist < h[j].dist }
func (h minHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x interface{}) { *h = append(*h, x.(item)) }
func (h *minHeap) Pop() interface{} {
	old := *h
	x := old[len(old)-1]
	*h = old[:len(old)-1]
	return x
}

func main() {
	graph := [][]edge{{{1, 4}, {2, 1}}, {{3, 1}}, {{1, 2}, {3, 5}}, {{4, 3}}, {}}
	dist := make([]int, len(graph))
	for i := range dist {
		dist[i] = math.MaxInt
	}
	dist[0] = 0
	h := &minHeap{{0, 0}}
	for h.Len() > 0 {
		top := heap.Pop(h).(item)
		if top.dist > dist[top.v] {
			continue // устаревшая запись
		}
		for _, e := range graph[top.v] {
			if nd := top.dist + e.w; nd < dist[e.to] {
				dist[e.to] = nd
				heap.Push(h, item{nd, e.to})
			}
		}
	}
	fmt.Println("Dijkstra from 0:", strings.Trim(fmt.Sprint(dist), "[]"))
}
