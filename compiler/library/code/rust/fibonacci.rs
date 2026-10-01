// Числа Фибоначчи как итератор: std::iter::successors генерирует пары (a, b).
fn fibonacci() -> impl Iterator<Item = u64> {
    std::iter::successors(Some((0u64, 1u64)), |&(a, b)| Some((b, a + b))).map(|(a, _)| a)
}

fn main() {
    let first: Vec<String> = fibonacci().take(15).map(|f| f.to_string()).collect();
    println!("Fibonacci: {}", first.join(" "));
    println!("F(50) = {}", fibonacci().nth(50).unwrap());
}
