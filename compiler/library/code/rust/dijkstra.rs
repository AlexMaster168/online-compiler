// Дейкстра с BinaryHeap: куча в Rust максимальная, поэтому кладём Reverse((dist, v)).
use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn main() {
    let graph: [&[(usize, u32)]; 5] = [&[(1, 4), (2, 1)], &[(3, 1)], &[(1, 2), (3, 5)], &[(4, 3)], &[]];
    let mut dist = [u32::MAX; 5];
    let mut heap = BinaryHeap::from([Reverse((0u32, 0usize))]);
    dist[0] = 0;
    while let Some(Reverse((d, v))) = heap.pop() {
        if d > dist[v] {
            continue; // устаревшая запись
        }
        for &(u, w) in graph[v] {
            if d + w < dist[u] {
                dist[u] = d + w;
                heap.push(Reverse((dist[u], u)));
            }
        }
    }
    let out: Vec<String> = dist.iter().map(|d| d.to_string()).collect();
    println!("Dijkstra from 0: {}", out.join(" "));
}
