// Решето Эратосфена: O(n log log n).
fn sieve(n: usize) -> Vec<usize> {
    let mut is_prime = vec![true; n + 1];
    is_prime[0] = false;
    is_prime[1] = false;
    let mut p = 2;
    while p * p <= n {
        if is_prime[p] {
            for k in (p * p..=n).step_by(p) {
                is_prime[k] = false;
            }
        }
        p += 1;
    }
    (0..=n).filter(|&i| is_prime[i]).collect()
}

fn main() {
    let primes: Vec<String> = sieve(50).iter().map(|p| p.to_string()).collect();
    println!("Primes up to 50: {}", primes.join(" "));
}
