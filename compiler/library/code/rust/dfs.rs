// Поиск в глубину рекурсией: O(V + E).
fn dfs(graph: &[&[usize]], v: usize, visited: &mut [bool], order: &mut Vec<usize>) {
    visited[v] = true;
    order.push(v);
    for &u in graph[v] {
        if !visited[u] {
            dfs(graph, u, visited, order);
        }
    }
}

fn main() {
    let graph: [&[usize]; 6] = [&[1, 2], &[0, 3], &[0, 4], &[1, 5], &[2, 5], &[3, 4]];
    let mut visited = [false; 6];
    let mut order = Vec::new();
    dfs(&graph, 0, &mut visited, &mut order);
    let out: Vec<String> = order.iter().map(|v| v.to_string()).collect();
    println!("DFS order: {}", out.join(" "));
}
