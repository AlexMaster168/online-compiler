// Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
fn knapsack(weights: &[usize], values: &[u32], capacity: usize) -> u32 {
    let mut dp = vec![0u32; capacity + 1];
    for (&w, &v) in weights.iter().zip(values) {
        for c in (w..=capacity).rev() {
            dp[c] = dp[c].max(dp[c - w] + v);
        }
    }
    dp[capacity]
}

fn main() {
    println!("Knapsack max value: {}", knapsack(&[1, 3, 4, 5], &[1, 4, 5, 7], 7));
}
