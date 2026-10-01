// Поиск в ширину: VecDeque как очередь, O(V + E).
use std::collections::VecDeque;

fn main() {
    let graph: [&[usize]; 6] = [&[1, 2], &[0, 3], &[0, 4], &[1, 5], &[2, 5], &[3, 4]];
    let mut dist = vec![-1i32; graph.len()];
    let mut order = Vec::new();
    let mut queue = VecDeque::from([0usize]);
    dist[0] = 0;
    while let Some(v) = queue.pop_front() {
        order.push(v.to_string());
        for &u in graph[v] {
            if dist[u] == -1 {
                dist[u] = dist[v] + 1;
                queue.push_back(u);
            }
        }
    }
    let dist: Vec<String> = dist.iter().map(|d| d.to_string()).collect();
    println!("BFS order: {}", order.join(" "));
    println!("Distances: {}", dist.join(" "));
}
