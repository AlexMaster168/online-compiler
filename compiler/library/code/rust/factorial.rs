// Факториал рекурсией. 20! — максимум для u64; переполнение в debug-сборке Rust ловит паникой.
fn factorial(n: u64) -> u64 {
    if n <= 1 { 1 } else { n * factorial(n - 1) }
}

fn main() {
    println!("10! = {}", factorial(10));
    println!("20! = {}", factorial(20));
}
